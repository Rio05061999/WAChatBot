# WAChatBot
LLM based WhatsApp Chat Bot with CRM 

WhatsApp - GreenAPI, NLP - OpenAIAPI, CRM - YcliensAPI.
Prompt is written to handle barbershop management tasks. Bot can provide human-like conversation with clients based on information from CRM about avaliable slots and staff.

The bot has problems with understanding the start of a new dialogue within a single chat. To solve this problem, the chat history is cleared every 20 minutes. But this is a kludge.
Prompt written for conversations in Russian.
Next step will be sending of new approval with clients to CRM as a slot.
