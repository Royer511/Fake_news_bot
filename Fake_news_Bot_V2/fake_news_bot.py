import os
import re
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
import discord
from transformers import pipeline
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Get Discord token from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize Discord bot with all intents
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

# Define keywords, blacklisted websites, and social media domains
FAKE_KEYWORDS = [
    "rumor", "sources", "allegedly", "unconfirmed", "speculation", "according to my",
    "insiders reveal", "it's believed", "people say", "word on the street", "conspiracy",
    "cover-up", "whistleblower claims", "leaked information suggests", "anonymous tip",
    "off-the-record", "take this with a grain of salt", "secret documents reveal",
    "unverified report", "controversial theory", "hidden agenda", "it's rumored",
    "behind closed doors", "unnamed source", "experts are divided", "hushed up"
]
BLACKLISTED_WEBSITES = [
    'theonion.com',        # Satirical news
    'babylonbee.com',      # Satirical news
    'worldnewsdailyreport.com', # Known for fake news stories
    'nationalreport.net',  # Known for fake news stories
    'infowars.com',        # Hyperpartisan and conspiracy theories
    'naturalnews.com',     # Misleading health claims
    'mercola.com',         # Misleading health claims
    'godlikeproductions.com', # Conspiracy theories
    'abovetopsecret.com',  # Conspiracy theories
    'breitbart.com'        # Hyperpartisan  # Add websites known for misleading info
]
SOCIAL_MEDIA_DOMAINS = [
    "twitter.com", "facebook.com", "instagram.com", 
    "linkedin.com", "reddit.com"
]

# Function to check if a domain is blacklisted
def is_blacklisted(domain):
    return domain in BLACKLISTED_WEBSITES

# Function to send warning messages
async def send_warning(channel, warning_text):
    await channel.send(f"⚠️ Warning: {warning_text}")
    
# Initialize the summarization pipeline
summarizer = pipeline("summarization")

# Event for receiving messages
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content_lower = message.content.lower()
    
    # Recognize and reply to 'good bot' interactions
    if "good bot" in content_lower and message.reference:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        if referenced_message.author == client.user:
            await message.channel.send("Thank you!")
    
    # Check for fake news keywords and issue warnings
    for keyword in FAKE_KEYWORDS:
        if keyword in content_lower:
            await send_warning(message.channel, f'Keyword "{keyword}" detected. Please verify the information before sharing.')
            break

    for website in BLACKLISTED_WEBSITES:
        if website in content_lower:
            await send_warning(message.channel, f'Website "{website}" is known for potentially misleading content.')
            break
    
    await client.process_commands(message)
    
# Command to check the credibility of a news source
@client.command()
async def checknews(ctx, link: str):
    parsed_uri = urlparse(link)
    domain = f"{parsed_uri.netloc}"
    
    if any(social_media in domain for social_media in SOCIAL_MEDIA_DOMAINS):
        await ctx.send("⚠️ Caution: This link is from a social media platform. Verify any claims or news with trusted sources.")
    elif is_blacklisted(domain):
        await ctx.send(f"⚠️ Warning: The domain {domain} is known for hosting misleading or false information.")
        
# Command to summarize article contents
@client.command(name='summary')
async def summary(ctx, url: str):
    try:
        if re.search(r'twitter\.com|facebook\.com|instagram\.com', url):
            await ctx.send("I can't summarize social media posts.")
            return

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all(['p', 'div', 'article'])
        article_text = ' '.join([para.text for para in paragraphs])[:2048]

        summarized_text = summarizer(article_text, max_length=600, min_length=100, do_sample=False)
        await ctx.send(summarized_text[0]['summary_text'])

    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# Command to show all available bot commands
@client.command(name='commands')
async def commands(ctx):
    help_text = """
    **Commands:**
    - `!summary <URL>`: Summarize the content of the given URL.
    - `!checknews <URL>`: Check if the URL is from a blacklisted or social media source.
    """
    embed = discord.Embed(title="Fake News Bot Help", description=help_text, color=0x3498db)
    await ctx.send(embed=embed)

# Run the bot
client.run(TOKEN)