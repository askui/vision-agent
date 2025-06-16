import {
  MessageContent,
  MessageContentText,
  MessageContentImage,
  MessageContentToolResult,
  MessageContentToolUse,
} from "@/lib/types";

interface TextContentProps {
  content: MessageContentText;
}

function TextContent({ content }: TextContentProps) {
  return (
    <div className="prose prose-sm max-w-none">
      <p className="whitespace-pre-wrap">{content.text}</p>
    </div>
  );
}

interface ImageContentProps {
  content: MessageContentImage;
}

function ImageContent({ content }: ImageContentProps) {
  const src =
    content.source?.type === "url"
      ? content.source.url
      : content.source?.type === "base64"
      ? `data:${content.source.media_type};base64,${content.source.data}`
      : "";

  return (
    <div className="max-w-md">
      <img
        src={src}
        alt="Uploaded image"
        className="rounded-lg border border-border"
      />
    </div>
  );
}

interface ToolResultContentProps {
  content: MessageContentToolResult;
}

function ToolResultContent({ content }: ToolResultContentProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm">
        <div
          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            content.is_error
              ? "bg-destructive/10 text-destructive"
              : "bg-green-500/10 text-green-500"
          }`}
        >
          {content.is_error ? "Failed" : "Success"}
        </div>
        <span className="text-muted-foreground">ID: {content.tool_use_id}</span>
      </div>
      <div className={content.is_error ? "text-destructive" : ""}>
        {typeof content.content === "string" ? (
          <TextContent content={{ type: "text", text: content.content }} />
        ) : (
          content.content.map((item, index) => {
            if (item.type === "text") {
              return <TextContent key={index} content={item} />;
            } else if (item.type === "image") {
              return <ImageContent key={index} content={item} />;
            }
            return null;
          })
        )}
      </div>
    </div>
  );
}

interface ToolUseContentProps {
  content: MessageContentToolUse;
}

function ToolUseContent({ content }: ToolUseContentProps) {
  return (
    <div className="rounded-md bg-muted p-3 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <div className="font-medium">Tool: {content.name}</div>
        <span className="text-muted-foreground">ID: {content.id}</span>
      </div>
      <pre className="mt-2 overflow-x-auto">
        {JSON.stringify(content.input, null, 2)}
      </pre>
    </div>
  );
}

interface MessageContentBlockProps {
  content: string | MessageContent[];
}

export function MessageContentBlock({ content }: MessageContentBlockProps) {
  if (typeof content === "string") {
    return <TextContent content={{ type: "text", text: content }} />;
  }

  return (
    <div className="space-y-3">
      {content.map((item, index) => {
        switch (item.type) {
          case "text":
            return <TextContent key={index} content={item} />;
          case "image":
            return <ImageContent key={index} content={item} />;
          case "tool_result":
            return <ToolResultContent key={index} content={item} />;
          case "tool_use":
            return <ToolUseContent key={index} content={item} />;
          default:
            return null;
        }
      })}
    </div>
  );
}
