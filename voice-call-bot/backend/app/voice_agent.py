import os
from openai import OpenAI
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

load_dotenv()

class VoiceAgent:
    def __init__(self):
        self.twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def create_call(self, to_number: str, customer_name: str, vehicle_model: str, 
                   call_type: str, last_service_date: str = None):
        """
        Initiate outbound call to customer
        """
        try:
            # Create TwiML for the call
            callback_url = f"{os.getenv('APP_HOST', 'http://localhost:8000')}/api/voice/handle"
            
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.twilio_number,
                url=callback_url,
                method='POST',
                status_callback=f"{os.getenv('APP_HOST', 'http://localhost:8000')}/api/voice/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_greeting(self, customer_name: str, vehicle_model: str, 
                         call_type: str, last_service_date: str = None) -> str:
        """
        Generate personalized greeting using OpenAI
        """
        if call_type == "reminder":
            prompt = f"""
            Buat greeting ramah dalam Bahasa Indonesia untuk mengingatkan customer service kendaraan.
            
            Detail:
            - Nama Customer: {customer_name}
            - Model Kendaraan: {vehicle_model}
            - Service Terakhir: {last_service_date}
            
            Greeting harus:
            1. Ramah dan profesional
            2. Menyebutkan nama customer
            3. Mengingatkan sudah waktunya service
            4. Menawarkan untuk booking jadwal
            5. Maksimal 3 kalimat
            
            Contoh: "Selamat pagi Pak/Bu {customer_name}, saya dari Toyota Denpasar. 
            Kami ingin mengingatkan bahwa {vehicle_model} Bapak/Ibu sudah waktunya untuk service rutin. 
            Apakah Bapak/Ibu berkenan untuk kami buatkan jadwal service?"
            """
        else:  # booking confirmation
            prompt = f"""
            Buat greeting ramah dalam Bahasa Indonesia untuk konfirmasi booking service.
            
            Detail:
            - Nama Customer: {customer_name}
            - Model Kendaraan: {vehicle_model}
            
            Greeting harus:
            1. Ramah dan profesional
            2. Menyebutkan nama customer
            3. Konfirmasi booking service
            4. Tanya jadwal yang diinginkan
            5. Maksimal 3 kalimat
            """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Anda adalah customer service Toyota yang ramah dan profesional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback greeting
            return f"Selamat pagi Pak/Bu {customer_name}, saya dari Toyota Denpasar. Kami ingin mengingatkan bahwa {vehicle_model} Bapak/Ibu sudah waktunya untuk service rutin. Apakah Bapak/Ibu berkenan untuk kami buatkan jadwal service?"
    
    def handle_response(self, user_input: str, context: dict) -> dict:
        """
        Process customer response using OpenAI
        """
        conversation_history = context.get("conversation_history", [])
        customer_name = context.get("customer_name", "")
        vehicle_model = context.get("vehicle_model", "")
        
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        system_prompt = f"""
        Anda adalah AI customer service Toyota Denpasar yang ramah dan profesional.
        
        Konteks:
        - Customer: {customer_name}
        - Kendaraan: {vehicle_model}
        - Tujuan: Booking service appointment
        
        Tugas Anda:
        1. Pahami respons customer
        2. Jika customer setuju, tanyakan jadwal yang diinginkan (tanggal dan jam)
        3. Jika customer menolak, tanyakan alasan dan tawarkan alternatif
        4. Jika customer bertanya, jawab dengan informasi yang relevan
        5. Selalu ramah dan profesional
        6. Gunakan Bahasa Indonesia yang sopan
        
        Respons Anda harus dalam format JSON:
        {{
            "message": "respons Anda ke customer",
            "intent": "agree|decline|question|schedule",
            "booking_confirmed": true/false,
            "scheduled_date": "YYYY-MM-DD" (jika ada),
            "scheduled_time": "HH:MM" (jika ada),
            "needs_followup": true/false
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *conversation_history
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(ai_response)
            except:
                # Fallback if not JSON
                result = {
                    "message": ai_response,
                    "intent": "unknown",
                    "booking_confirmed": False,
                    "needs_followup": True
                }
            
            conversation_history.append({
                "role": "assistant",
                "content": result["message"]
            })
            
            result["conversation_history"] = conversation_history
            return result
            
        except Exception as e:
            return {
                "message": "Maaf, saya mengalami kendala. Apakah Bapak/Ibu bisa mengulangi?",
                "intent": "error",
                "booking_confirmed": False,
                "needs_followup": True,
                "conversation_history": conversation_history,
                "error": str(e)
            }
    
    def create_twiml_response(self, message: str, gather: bool = True) -> str:
        """
        Create TwiML response for Twilio
        """
        response = VoiceResponse()
        
        if gather:
            gather_obj = Gather(
                input='speech',
                language='id-ID',
                timeout=5,
                speech_timeout='auto',
                action='/api/voice/process',
                method='POST'
            )
            gather_obj.say(message, language='id-ID', voice='Polly.Joanna')
            response.append(gather_obj)
            
            # If no input, redirect
            response.redirect('/api/voice/handle')
        else:
            response.say(message, language='id-ID', voice='Polly.Joanna')
            response.hangup()
        
        return str(response)
    
    def calculate_next_service_date(self, last_service_date: datetime, 
                                   service_interval_months: int = 6) -> datetime:
        """
        Calculate next service date based on last service
        """
        if last_service_date:
            return last_service_date + timedelta(days=service_interval_months * 30)
        return datetime.now()
    
    def should_remind_service(self, last_service_date: datetime, 
                             reminder_days_before: int = 7) -> bool:
        """
        Check if customer should be reminded for service
        """
        if not last_service_date:
            return True
        
        next_service = self.calculate_next_service_date(last_service_date)
        reminder_date = next_service - timedelta(days=reminder_days_before)
        
        return datetime.now() >= reminder_date
