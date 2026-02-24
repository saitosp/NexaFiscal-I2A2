# Palette's Journal

## 2026-02-24 - File Preview Feedback
**Learning:** Users (and developers) value immediate visual confirmation of uploads, especially for document processing. The use of `st.expander` expanded by default for images provides this confirmation without cluttering the UI permanently if the user wants to collapse it.
**Action:** When implementing file uploads in data processing apps, always include a preview mechanism that handles multiple file types gracefully (Image vs XML vs PDF) and uses collapsible containers to manage screen real estate.
