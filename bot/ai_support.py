import os
from google.genai import GoogleGenAI

class AISupport:
    def __init__(self):
        self.client = GoogleGenAI(api_key=os.getenv("GEMINI_API_KEY"))
        self.system_instruction = """
        Сен - DigitalShop дүкенінің көмекшісісің. 
        Пайдаланушыларға Stars, Premium сатып алу және NFT жалдау туралы сұрақтарға жауап бер.
        Жауаптарың қысқа, нұсқа және қазақ тілінде (немесе сұрақ қойылған тілде) болуы керек.
        Егер сұрақ дүкенге қатысты болмаса, сыпайы түрде тек дүкен бойынша көмектесе алатыныңды айт.
        """

    async def ask(self, question: str) -> str:
        try:
            response = await self.client.models.generateContent({
                "model": "gemini-2.0-flash-exp",
                "contents": question,
                "config": {"systemInstruction": self.system_instruction}
            })
            return response.text
        except Exception as e:
            print(f"AI Error: {e}")
            return "Кешіріңіз, қазір жауап бере алмаймын. Кейінірек қайталаңыз."
