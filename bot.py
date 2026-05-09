import discord
from discord import app_commands
import os
import aiohttp
import tempfile
from dotenv import load_dotenv
from pdf_generator import generate_addendum
from parse_addendum import extract_fields

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise SystemExit("DISCORD_TOKEN env var is required")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Tracks in-progress addendum sessions per user
sessions = {}

STEPS = [
    ("addendum_number",  "What **addendum number** is this? (e.g. `1`, `2`, `3`)"),
    ("doc_type",         "Is this an **Addendum** or a **Counteroffer**? (type one)"),
    ("offer_ref_date",   "What is the **Offer Reference Date** on the original contract? (e.g. `5th day of April, 2026`)"),
    ("buyer_name",       "What is the **Buyer's full name**?"),
    ("seller_name",      "What is the **Seller's full name**? (e.g. `Edge Homes Utah, LLC`)"),
    ("property_address", "What is the **property address**? (include city, state, zip)"),
    ("terms",            "Enter the **terms** for this addendum.\nType all numbered terms and send when done.\n_(Example: `1. Seller agrees to... 2. All other terms accepted.`)_"),
]

DEFAULTS = {
    "acceptor":     "seller",
    "accept_time":  "N/A",
    "accept_ampm":  "AM",
    "accept_date":  "N/A",
}


@client.event
async def on_ready():
    await tree.sync()
    print(f"[bot] Logged in as {client.user} — slash commands synced.")


@tree.command(name="addendum", description="Generate a filled REPC Addendum PDF")
async def addendum_cmd(interaction: discord.Interaction):
    user_id = interaction.user.id
    sessions[user_id] = {"step": 0, "data": {}}

    await interaction.response.send_message(
        "Let's build your addendum. I'll ask you a few questions.\n\n"
        f"**Question 1 of {len(STEPS)}:** {STEPS[0][1]}",
        ephemeral=True
    )


UPLOAD_STEPS = [
    ("addendum_number", "What is the **new addendum number**? (e.g. `2`, `3`)"),
    ("terms",           "Enter the **new terms** for this addendum.\n_(Example: `1. Price to be $500,000. 2. All other terms remain the same.`)_"),
]

upload_sessions = {}


@tree.command(name="upload_addendum", description="Upload an existing addendum (PDF or photo) to pre-fill the next one")
async def upload_addendum_cmd(interaction: discord.Interaction):
    upload_sessions[interaction.user.id] = {"step": -1, "data": {}}
    await interaction.response.send_message(
        "Send your addendum as a **file or photo** in this channel and I'll read it automatically.",
        ephemeral=True
    )


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    user_id = message.author.id

    if user_id in upload_sessions:
        session = upload_sessions[user_id]
        step = session["step"]

        if step == -1:
            if not message.attachments:
                await message.channel.send("Please send a file or photo.")
                return

            attachment = message.attachments[0]
            async with aiohttp.ClientSession() as http:
                async with http.get(attachment.url) as resp:
                    file_bytes = await resp.read()

            content_type = attachment.content_type or ""
            if "pdf" in content_type:
                ext = ".pdf"
            elif "png" in content_type:
                ext = ".png"
            elif "jpeg" in content_type or "jpg" in content_type:
                ext = ".jpg"
            elif "heic" in content_type or "heif" in content_type:
                ext = ".heic"
            elif "webp" in content_type:
                ext = ".webp"
            elif "." in attachment.filename:
                ext = "." + attachment.filename.rsplit(".", 1)[-1].lower()
            else:
                ext = ".jpg"

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                extracted = extract_fields(tmp_path)
            except Exception as e:
                await message.channel.send(f"Failed to read file: {e}")
                del upload_sessions[user_id]
                return

            extracted.pop("accept_time", None)
            extracted.pop("accept_date", None)
            session["data"] = extracted
            session["step"] = 0

            summary = (
                f"Got it! Here's what I found:\n"
                f"- **Buyer:** {extracted.get('buyer_name', '?')}\n"
                f"- **Seller:** {extracted.get('seller_name', '?')}\n"
                f"- **Address:** {extracted.get('property_address', '?')}\n"
                f"- **Offer Ref Date:** {extracted.get('offer_ref_date', '?')}\n\n"
                f"Now let's fill in the new addendum.\n\n"
                f"**Question 1 of {len(UPLOAD_STEPS)}:** {UPLOAD_STEPS[0][1]}"
            )
            await message.channel.send(summary)
            return

        if step < len(UPLOAD_STEPS):
            field_key, _ = UPLOAD_STEPS[step]
            answer = message.content.strip()

            if not answer:
                await message.channel.send("Please enter a value to continue.")
                return

            session["data"][field_key] = answer
            session["step"] += 1
            next_step = session["step"]

            if next_step < len(UPLOAD_STEPS):
                _, next_question = UPLOAD_STEPS[next_step]
                await message.channel.send(f"**Question {next_step + 1} of {len(UPLOAD_STEPS)}:** {next_question}")
            else:
                await message.channel.send("Generating your addendum PDF...")
                try:
                    full_data = {**DEFAULTS, **session["data"]}
                    pdf_path = generate_addendum(full_data)
                    buyer = full_data.get("buyer_name", "buyer")
                    addr = full_data.get("property_address", "")
                    await message.channel.send(
                        f"Here is your addendum for **{buyer}** — {addr}:",
                        file=discord.File(pdf_path)
                    )
                except Exception as e:
                    await message.channel.send(f"Error generating PDF: {e}")
                finally:
                    del upload_sessions[user_id]
        return

    if user_id not in sessions:
        return

    session = sessions[user_id]
    step = session["step"]

    if step >= len(STEPS):
        return

    field_key, _ = STEPS[step]
    answer = message.content.strip()

    if not answer:
        await message.channel.send("Please enter a value to continue.")
        return

    if field_key == "doc_type":
        answer = "counteroffer" if "counter" in answer.lower() else "addendum"
    if field_key == "acceptor":
        answer = "buyer" if "buyer" in answer.lower() else "seller"
    if field_key == "accept_ampm":
        answer = "PM" if "pm" in answer.lower() else "AM"

    session["data"][field_key] = answer
    session["step"] += 1
    next_step = session["step"]

    if next_step < len(STEPS):
        _, next_question = STEPS[next_step]
        await message.channel.send(f"**Question {next_step + 1} of {len(STEPS)}:** {next_question}")
    else:
        await message.channel.send("Generating your addendum PDF...")
        try:
            full_data = {**DEFAULTS, **session["data"]}
            pdf_path = generate_addendum(full_data)
            buyer = full_data.get("buyer_name", "buyer")
            addr = full_data.get("property_address", "")
            await message.channel.send(
                f"Here is your addendum for **{buyer}** — {addr}:",
                file=discord.File(pdf_path)
            )
        except Exception as e:
            await message.channel.send(f"Error generating PDF: {e}")
        finally:
            del sessions[user_id]


client.run(DISCORD_TOKEN)
