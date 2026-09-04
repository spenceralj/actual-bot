import discord

import agent

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user in message.mentions:
        prompt = message.clean_content.replace(f"@{client.user.name if client.user else None}", "").strip()

        async with message.channel.typing():
            try:
                response = await agent.ask(prompt)
                await message.reply(response or "I couldn't find any financial records for that.")
            except Exception as e:
                print(f"Error in ask(): {e}")
                await message.reply(f"⚠️ An error occurred: `{e}`")
