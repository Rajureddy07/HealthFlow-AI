import easyocr


class OCRService:

    def __init__(self):
        self.reader = easyocr.Reader(
            ["en"],
            gpu=False
        )

    def extract_text(self, image_path: str):
        results = self.reader.readtext(image_path)

        extracted_text = []

        for result in results:
            text = result[1]
            confidence = result[2]

            extracted_text.append({
                "text": text,
                "confidence": round(float(confidence), 4)
            })

        return extracted_text