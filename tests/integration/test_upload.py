import pymupdf
import pytest

pytestmark = pytest.mark.integration


def _make_pdf(text: str = "Hello, this is test content.") -> bytes:
    """Create a minimal PDF in memory."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestUploadEndpoint:
    async def test_upload_pdf_returns_201(self, async_client, test_api_key):
        raw_key, _ = test_api_key
        pdf_bytes = _make_pdf()

        response = await async_client.post(
            "/api/v1/upload",
            headers={"x-api-key": raw_key},
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["status"] == "processed"
        assert data["mime_type"] == "application/pdf"

    async def test_upload_rejects_non_pdf(self, async_client, test_api_key):
        raw_key, _ = test_api_key

        response = await async_client.post(
            "/api/v1/upload",
            headers={"x-api-key": raw_key},
            files={"file": ("readme.txt", b"plain text", "text/plain")},
        )

        assert response.status_code == 415

    async def test_upload_returns_403_with_invalid_key(self, async_client):
        pdf_bytes = _make_pdf()

        response = await async_client.post(
            "/api/v1/upload",
            headers={"x-api-key": "invalid-key"},
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 403
