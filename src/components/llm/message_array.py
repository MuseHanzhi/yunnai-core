from .types import ResourceOptions

class MessageArray:
    def __iter__(self):
        return iter(self.messages)

    def __init__(self, array: list[ResourceOptions] | None = None):
        self.messages: list[ResourceOptions] = array if array else []
    
    def add_image(self, image_url: str):
        self.messages.append({
            "type": "image",
            "image_url": image_url
        })
        return self
    
    def add_audio(self, audio_url: str):
        self.messages.append({
            "type": "audio",
            "input_audio": audio_url
        })
        return self
    
    def add_file(self, file_url: str):
        self.messages.append({
            "type": "file",
            "file": file_url
        })
        return self
    
    def add_text(self, text: str):
        self.messages.append({
            "type": "text",
            "text": text
        })
        return self
