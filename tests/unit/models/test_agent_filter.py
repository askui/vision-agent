from askui.models.shared.agent import Agent
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
    ToolResultBlockParam,
)


def make_image_block() -> ImageBlockParam:
    return ImageBlockParam(
        source=Base64ImageSourceParam(
            media_type="image/png",
            data="abc",
        ),
    )


def make_tool_result_block(num_images: int, num_texts: int = 0) -> ToolResultBlockParam:
    content = [make_image_block() for _ in range(num_images)] + [
        TextBlockParam(text=f"text{i}") for i in range(num_texts)
    ]
    return ToolResultBlockParam(tool_use_id="id", content=content)


def make_message_with_tool_result(num_images: int, num_texts: int = 0) -> MessageParam:
    return MessageParam(
        role="user", content=[make_tool_result_block(num_images, num_texts)]
    )


def test_no_images() -> None:
    messages = [make_message_with_tool_result(0, 2)]
    filtered = Agent._maybe_filter_to_n_most_recent_images(messages, 3, 2)
    assert filtered == messages


def test_fewer_images_than_keep() -> None:
    messages = [make_message_with_tool_result(2, 1)]
    filtered = Agent._maybe_filter_to_n_most_recent_images(messages, 3, 2)
    # Only ToolResultBlockParam with list content should be checked
    all_images = [
        c
        for m in filtered
        for b in (m.content if isinstance(m.content, list) else [])
        if isinstance(b, ToolResultBlockParam) and isinstance(b.content, list)
        for c in b.content
        if getattr(c, "type", None) == "image"
    ]
    expected_images = [
        c
        for b in (messages[0].content if isinstance(messages[0].content, list) else [])
        if isinstance(b, ToolResultBlockParam) and isinstance(b.content, list)
        for c in b.content
        if getattr(c, "type", None) == "image"
    ]
    assert all_images == expected_images


def test_exactly_images_to_keep() -> None:
    messages = [make_message_with_tool_result(3, 1)]
    filtered = Agent._maybe_filter_to_n_most_recent_images(messages, 3, 2)
    # Only check .content if the type is correct
    first_block = (
        filtered[0].content[0]
        if isinstance(filtered[0].content, list) and len(filtered[0].content) > 0
        else None
    )
    if isinstance(first_block, ToolResultBlockParam) and isinstance(
        first_block.content, list
    ):
        assert len(first_block.content) == 4
    else:
        error_msg = (
            "filtered[0].content[0] is not a ToolResultBlockParam with list content"
        )
        raise AssertionError(error_msg)  # noqa: TRY004
    all_tool_result_contents = [
        c
        for m in filtered
        for b in (m.content if isinstance(m.content, list) else [])
        if isinstance(b, ToolResultBlockParam) and isinstance(b.content, list)
        for c in b.content
    ]
    assert (
        sum(1 for c in all_tool_result_contents if getattr(c, "type", None) == "image")
        == 3
    )


def test_more_images_than_keep_removes_oldest() -> None:
    messages = [
        make_message_with_tool_result(2, 0),
        make_message_with_tool_result(2, 0),
    ]
    filtered = Agent._maybe_filter_to_n_most_recent_images(messages, 2, 2)
    # Only 2 images should remain, and they should be the newest (from the last message)
    all_images = [
        c
        for m in filtered
        for b in (m.content if isinstance(m.content, list) else [])
        if isinstance(b, ToolResultBlockParam) and isinstance(b.content, list)
        for c in b.content
        if getattr(c, "type", None) == "image"
    ]
    assert len(all_images) == 2
    # They should be from the last message
    assert all_images == [
        c
        for b in (filtered[1].content if isinstance(filtered[1].content, list) else [])
        if isinstance(b, ToolResultBlockParam) and isinstance(b.content, list)
        for c in b.content[:2]
        if getattr(c, "type", None) == "image"
    ]


def test_removal_chunking() -> None:
    messages = [make_message_with_tool_result(5, 0)]
    filtered = Agent._maybe_filter_to_n_most_recent_images(messages, 2, 2)
    # Should remove 4 (chunk of 4), leaving 1 image
    all_images = [
        c
        for m in filtered
        for b in (m.content if isinstance(m.content, list) else [])
        if isinstance(b, ToolResultBlockParam) and isinstance(b.content, list)
        for c in b.content
        if getattr(c, "type", None) == "image"
    ]
    assert len(all_images) == 3
