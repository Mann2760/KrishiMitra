import os
import tempfile
import unittest

# Set a temporary SQLite path before importing app.
fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(fd)
os.environ["SQLITE_PATH"] = db_path
os.environ["USE_FIRESTORE"] = "false"
os.environ.pop("GEMINI_API_KEY", None)

import app as app_module


class KrishiMitraTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_missing_fields_rejected(self):
        response = self.client.post("/api/advisory", json={"crop": "Cotton"})
        self.assertEqual(response.status_code, 400)

    def test_create_and_read_advisory(self):
        response = self.client.post("/api/advisory", json={
            "crop": "Cotton",
            "location": "Demo district",
            "growth_stage": "Vegetative growth",
            "symptoms": "Some leaves have yellow patches",
            "language": "English"
        })
        self.assertEqual(response.status_code, 201)
        item = response.json
        self.assertIn("id", item)
        self.assertIn("advisory", item)
        detail = self.client.get(f"/api/advisories/{item['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json["id"], item["id"])

    def test_feedback(self):
        created = self.client.post("/api/advisory", json={
            "crop": "Rice", "location": "Demo district",
            "growth_stage": "Seedling", "symptoms": "Leaves look pale",
            "language": "English"
        }).json
        response = self.client.post("/api/feedback", json={
            "advisory_id": created["id"], "rating": 5, "comment": "Clear"
        })
        self.assertEqual(response.status_code, 201)

    def test_invalid_language_rejected(self):
        response = self.client.post("/api/advisory", json={
            "crop": "Rice", "location": "Demo district",
            "growth_stage": "Seedling", "symptoms": "Pale leaves",
            "language": "French"
        })
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
