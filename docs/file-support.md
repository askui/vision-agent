# File Format Support in AskUI Python SDK

This document provides comprehensive information about how different file formats are supported in the AskUI Python SDK, including their processing methods and integration with Large Language Models (LLMs).

## Supported File Formats

The AskUI Python SDK supports the following file formats for data extraction and processing:

### 📄 PDF Files (.pdf)

- **MIME Types**: `application/pdf`
- **Maximum File Size**: 20MB
- **Processing Method**: **Depends on Usage Context**


#### ComputerAgent.get() Usage (No History)

- **Per-Query Processing**: Each `get()` command processes the PDF file directly, no history is maintained
- **Always processes original file**: Every query runs against the original PDF file, not cached content
- **No extraction caching**: File is processed fresh for each separate `get()` call
- **Architecture**: PDF → Gemini (direct processing) → Return results → No storage
- **Model Support**:
  - ✅ **ComputerAgent.get()**: AskUI Gemini models process PDF directly for each query

#### Processing Workflow for PDF Files


**ComputerAgent.get() Workflow (Per-query processing):**

```mermaid
graph TD
    A[Call agent.get with PDF] --> B[Load as PdfSource]
    B --> C[Send directly as binary to Gemini]
    C --> D[Gemini processes content]
    D --> E[Return results directly]
    E --> F[No storage - process again for next call]
```

#### PDF-Specific Limitations

- **20MB file size limit** for PDF files
- **Processing model restriction**: Only AskUI-hosted Gemini models can process PDFs
- **No caching mechanism**: PDF content is re-extracted on every run 
- **Performance impact**:
  - ComputerAgent.get(): PDF processed for each individual query
- **Multiple PDF overhead**: All PDF files are re-processed on every run
- **Future enhancement**: Caching mechanism may be implemented to avoid repeated extraction

### 📊 Excel Files (.xlsx, .xls)

- **MIME Types**:
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (.xlsx)
  - `application/vnd.ms-excel` (.xls)
- **Processing Method**: **Depends on Usage Context**

#### ComputerAgent.get() Usage (No History)

- **Per-Query Processing**: Each `get()` command converts the Excel file to markdown fresh, no history is maintained
- **Always processes original file**: Every query runs against the original Excel file, not cached content
- **No conversion caching**: File is converted fresh for each separate `get()` call
- **Architecture**: Excel → `markitdown` conversion → Gemini processing → Return results → No storage
- **Features**:
  - Sheet names are preserved in the markdown output
  - Tables are converted to markdown table format
  - Optimized for LLM token usage
  - Deterministic conversion process (same input = same output)
  - **No AI in conversion**: `markitdown` performs rule-based conversion
- **Model Support**:
  - ✅ **ComputerAgent.get()**: Only Gemini models can process converted markdown for each query

#### Processing Workflow for Excel Files


**ComputerAgent.get() Workflow (Per-query conversion):**

```mermaid
graph TD
    A[Call agent.get with Excel] --> B[Load as OfficeDocumentSource]
    B --> C[Convert to Markdown using markitdown - NO AI]
    C --> D[Process with Gemini]
    D --> E[Return results directly]
    E --> F[No storage - convert again for next call]
```

#### Excel-Specific Limitations

- **No specific file size limit** mentioned (limited by general upload constraints)
- **No caching mechanism**: Excel content is re-converted on every run 
- Conversion quality depends on [`markitdown`](https://github.com/microsoft/markitdown) library capabilities
- Complex formatting may be simplified during markdown conversion
- Embedded objects (charts, complex tables) may not preserve all details
- **Processing model differences**:
  - ComputerAgent.get(): Only Gemini models can process converted content
- **No AI in conversion**: Conversion is deterministic and rule-based, not AI-powered
- **Performance impact**:
  - ComputerAgent.get(): Excel converted for each individual query
- **Multiple file overhead**: All Excel files are re-processed on every run
- **Future enhancement**: Caching mechanism may be implemented to avoid repeated conversion

### 📝 Word Documents (.doc, .docx)

- **MIME Types**:
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (.docx)
  - `application/msword` (.doc)
- **Processing Method**: **Depends on Usage Context**


#### ComputerAgent.get() Usage (No History)

- **Per-Query Processing**: Each `get()` command converts the Word file to markdown fresh, no history is maintained
- **Always processes original file**: Every query runs against the original Word file, not cached content
- **No conversion caching**: File is converted fresh for each separate `get()` call
- **Architecture**: Word → `markitdown` conversion → Gemini processing → Return results → No storage
- **Features**:
  - Layout and formatting preserved as much as possible
  - Tables converted to HTML tables within markdown
  - Deterministic conversion process (same input = same output)
  - No AI-generated image descriptions during conversion (handled by `markitdown`)
  - **No AI in conversion**: `markitdown` performs rule-based conversion
- **Model Support**:
  - ✅ **ComputerAgent.get()**: Only Gemini models can process converted markdown for each query

#### Processing Workflow for Word Documents


**ComputerAgent.get() Workflow (Per-query conversion):**

```mermaid
graph TD
    A[Call agent.get with Word] --> B[Load as OfficeDocumentSource]
    B --> C[Convert to Markdown using markitdown - NO AI]
    C --> D[Process with Gemini]
    D --> E[Return results directly]
    E --> F[No storage - convert again for next call]
```

#### Word Document-Specific Limitations

- **No specific file size limit** mentioned (limited by general upload constraints)
- **No caching mechanism**: Word content is re-converted on every run 
- Conversion quality depends on [`markitdown`](https://github.com/microsoft/markitdown) library capabilities
- Complex formatting may be simplified during markdown conversion
- Embedded objects (charts, complex tables) may not preserve all details
- **Processing model differences**:
  - ComputerAgent.get(): Only Gemini models can process converted content
- **No AI in conversion**: Conversion is deterministic and rule-based, not AI-powered
- **Performance impact**:
  - ComputerAgent.get(): Word converted for each individual query
- **Multiple file overhead**: All Word files are re-processed on every run
- **Future enhancement**: Caching mechanism may be implemented to avoid repeated conversion

### 📈 CSV Files (.csv)

- **Status**: **Not directly supported by the backend**
- **Note**: No specific CSV processing logic was found in the backend codebase, suggesting frontend preprocessing

#### Processing Workflow for CSV Files

```mermaid
graph TD
    A[Upload CSV] --> B[Frontend Processing]
    B --> C[Convert to Text/Table Format]
    C --> D[Send as Message Content]
    D --> E[Process as Regular Text by LLM]
```

#### CSV-Specific Limitations

- **No backend support**: CSV processing happens on the frontend only
- **Limited functionality**: No specialized CSV parsing or structure preservation
- **Text-only processing**: Treated as regular text content by the LLM
- **No file size limits**: Since processing happens on frontend, backend file limits don’t apply


## Technical Implementation Details

### Key Components

#### 1. Source Utilities (`src/askui/utils/source_utils.py`)

- Handles file type detection and source loading
- Supports MIME types: PDF, Excel (.xlsx, .xls), Word (.docx, .doc)
- Creates appropriate source objects (`PdfSource`, `OfficeDocumentSource`, `ImageSource`)

#### 2. Markdown Conversion (`src/askui/utils/markdown_utils.py`)

- Uses Microsoft’s [`markitdown`](https://github.com/microsoft/markitdown) library for Office document conversion
- Provides `convert_to_markdown()` function for file-to-markdown conversion
- **No AI involved**: `markitdown` performs deterministic, rule-based conversion
- Supports multiple formats: PDF, PowerPoint(used), Word (used), Excel (used), Images, Audio, HTML, and more

#### 3. Model-Specific Processing

- **Google Gemini API** (`src/askui/models/askui/google_genai_api.py`):
  - **Initial Processing Only**: Direct PDF processing (binary data) and Office document processing during upload
  - Currently the only models that support initial document processing during upload
- **Anthropic Models**: Can process extracted document text from chat history, primary LLM for computer use tasks


### Dependencies

The following key dependencies enable file format support:

- `markitdown[xls,xlsx,docx]>=0.1.2`: Non-AI Office document conversion during upload (see [Microsoft MarkItDown](https://github.com/microsoft/markitdown))
- `filetype>=1.2.0`: MIME type detection
- `google-genai>=1.20.0`: One-time PDF processing during upload for Gemini models

## Usage Examples

### Processing Excel Files

#### Using ComputerAgent.get() (Per-query conversion)

```python
from askui import ComputerAgent
from askui.models.models import ModelName
with ComputerAgent() as agent:
    # Excel converted to markdown fresh for each get() call - no history maintained    result1 = agent.get(
        "Extract the quarterly sales data",
        source="sales_report.xlsx",  # File converted to markdown each time        model=ModelName.ASKUI__GEMINI__2_5__FLASH  # Only Gemini models support documents    )
    # This call converts the Excel to markdown again from scratch    result2 = agent.get(
        "Find the highest revenue month",
        source="sales_report.xlsx",  # File converted again, no cached content        model=ModelName.ASKUI__GEMINI__2_5__FLASH
    )
```

### Processing PDF Files

#### Using ComputerAgent.get() (Per-query processing)

```python
from askui import ComputerAgent
from askui.models.models import ModelName
with ComputerAgent() as agent:
    # PDF processed fresh for each get() call - no history maintained    result1 = agent.get(
        "Summarize the main points",
        source="document.pdf",  # File processed directly each time        model=ModelName.ASKUI__GEMINI__2_5__FLASH  # Only Gemini models support PDFs    )
    # This call processes the PDF again from scratch    result2 = agent.get(
        "Extract key dates",
        source="document.pdf",  # File processed again, no cached content        model=ModelName.ASKUI__GEMINI__2_5__FLASH
    )
```

### Processing Word Documents

#### Using ComputerAgent.get() (Per-query conversion)

```python
from askui import ComputerAgent
from askui.models.models import ModelName
with ComputerAgent() as agent:
    # Word converted to markdown fresh for each get() call - no history maintained    result1 = agent.get(
        "Extract all action items",
        source="meeting_notes.docx",  # File converted to markdown each time        model=ModelName.ASKUI__GEMINI__2_5__FLASH  # Only Gemini models support documents    )
    # This call converts the Word document to markdown again from scratch    result2 = agent.get(
        "Find all mentioned dates",
        source="meeting_notes.docx",  # File converted again, no cached content        model=ModelName.ASKUI__GEMINI__2_5__FLASH
    )
```


## General Limitations and Considerations

- **Processing Model Restriction**: Currently, only Gemini models support document processing
- **No Caching Mechanism**: All document files (PDF, Excel, Word) are re-processed on every ComputerAgent.get() call
- **File Storage Only**: Files are stored as original files, not as extracted/converted content
- **Runtime Conversion**: Document processing happens on runtime to create LLM-compatible messages
- **Performance Impact**: Multiple documents mean multiple processing operations on every run

### Performance Considerations

- **No caching**: All document files are re-processed on every ComputerAgent.get() call
- **Multiple file overhead**: Having multiple documents significantly impacts performance as all are re-processed
- **Processing types**:
  - PDFs: Re-extracted by Gemini on every run (AI processing overhead)
  - Office documents: Re-converted by `markitdown` on every run (fast, deterministic, no AI overhead)
- Currently limited to Gemini models for document processing, which may create processing bottlenecks

## Model Compatibility Matrix

| File Format         | AskUI Gemini                             | Anthropic Claude                          | OpenRouter                                | AskUI Inference API                       |
| ------------------- | ---------------------------------------- | ----------------------------------------- | ----------------------------------------- | ----------------------------------------- |
| PDF (.pdf)          | ✅  | ❌ | ❌ | ❌ |
| Excel (.xlsx, .xls) | ✅                 | ✅  | ✅  | ✅  |
| Word (.docx, .doc)  | ✅ | ✅  | ✅  | ✅  |

**Legend:**

- ✅ Fully Supported
- ⚠️ Limited Support
- ❌ Not Supported

## Best Practices

1. **Understand Model Usage**:
   - **PDFs**: Only Gemini models can process PDFs 
   - **Office docs (ComputerAgent.get())**: Only Gemini models can process converted content
2. **Understand Processing Flow**:
   - Office docs (ComputerAgent.get()): `markitdown` (non-AI) conversion → Gemini processes converted content
   - PDFs: Direct binary processing by Gemini on every run/query → No caching
3. **Optimize File Size**: Keep PDF files under 20MB (required limit); Office documents have no specific size limit
4. **Test Document Quality**: Verify that processed documents maintain essential information
5. **Handle CSV Frontend**: Implement CSV processing on the frontend before sending to the API

## Future Enhancements

Potential areas for improvement:

- **PDF Caching Mechanism**: Implement caching to avoid re-extracting PDF content on every run
- **Expand Model Support**: Enable document processing for other models (Anthropic, OpenRouter, etc.)
- **Native CSV Support**: Add backend CSV processing capabilities
- **Additional Formats**: Support for PowerPoint, RTF, and other document formats
- **Enhanced Processing Pipeline**: Optimize document conversion and query processing
- **Improved Formatting**: Better preservation of complex document structures
- **Larger PDF Support**: Streaming processing for PDF files larger than 20MB
- **Multi-Model Architecture**: Allow different models for document extraction vs. computer use tasks
- **Intelligent Caching**: Cache extracted content
