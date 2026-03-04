#!/usr/bin/env python3
import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

ASSISTANT_NAME = os.getenv("VOICE_ASSISTANT_NAME", "Burt")
VOICE = os.getenv("TWILIO_TTS_VOICE", "Polly.Joanna-Neural")


def local_reply(user_text: str) -> str:
    t = (user_text or "").strip()
    if not t:
        return "I did not catch that. Could you repeat it?"

    # Lightweight local fallback behavior. Replace with model call later if desired.
    if "status" in t.lower():
        return "Current status: systems are online and I am available."
    if "bye" in t.lower() or "goodbye" in t.lower():
        return "Got it. Talk soon."
    return f"I heard: {t}. What would you like me to do next?"


@app.post("/voice")
def voice_entry():
    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/process-speech",
        method="POST",
        speech_timeout="auto",
        timeout=5,
    )
    gather.say(f"Hi, this is {ASSISTANT_NAME}. I am listening.", voice=VOICE)
    resp.append(gather)
    resp.redirect("/voice")
    return str(resp)


@app.post("/process-speech")
def process_speech():
    user_text = request.form.get("SpeechResult", "")
    reply = local_reply(user_text)

    resp = VoiceResponse()
    resp.say(reply, voice=VOICE)

    if "talk soon" in reply.lower():
        resp.hangup()
        return str(resp)

    gather = Gather(
        input="speech",
        action="/process-speech",
        method="POST",
        speech_timeout="auto",
        timeout=5,
    )
    gather.say("Anything else?", voice=VOICE)
    resp.append(gather)
    resp.redirect("/voice")
    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8787")), debug=False)
