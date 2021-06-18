import discord
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from collections import Counter

load_dotenv()

print('Application started')

# Get configuration from .env
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

CHANNELS_TO_SEARCH = os.getenv('CHANNELS_TO_SEARCH', [])
CHANNEL_TO_POST_IN = os.getenv('CHANNEL_TO_POST_IN')
COUNT_ALL_REACTIONS = os.getenv('COUNT_ALL_REACTIONS', 'True').lower() in ('true', '1', 't')
MESSAGE_ABOVE_THRESHOLD = os.getenv('MESSAGE_ABOVE_THRESHOLD','Congratulations _user_mention_')
MESSAGE_BELOW_THRESHOLD = os.getenv('MESSAGE_BELOW_THRESHOLD', '')
MESSAGE_HEADER = os.getenv('MESSAGE_HEADER','Which users received the most reactions today?')
MESSAGE_LIMIT = int(os.getenv('MESSAGE_LIMIT', '5000'))
REACTION_LIST = os.getenv('REACTION_LIST')
SEARCH_ALL_CHANNELS = os.getenv('SEARCH_ALL_CHANNELS', 'True').lower() in ('true', '1', 't')
REACTION_THRESHOLD = int(os.getenv('REACTION_THRESHOLD', '0'))

client = discord.Client()

yesterday_date_time = datetime.now() - timedelta(days = 1)

@client.event
async def on_ready():
  print('Discord client ready')

  # guild variable will be accessible outside the loop
  for guild in client.guilds:
        if guild.name == GUILD:
            break

  channels = guild.channels;

  print('Channels retrieved')

  reaction_count = {}
  reaction_breakdown = {}

  for channel in channels:
    # Skip categories and voice channels
    if channel is None or isinstance(channel, discord.CategoryChannel) or isinstance(channel, discord.VoiceChannel):
      continue

    # Skip channel if we aren't searching all channels and it is not in the list of channels to search
    if not SEARCH_ALL_CHANNELS and channel not in CHANNELS_TO_SEARCH:
      continue

    # Get messages from the previous day 
    try:
      messages = await channel.history(after=yesterday_date_time, limit=MESSAGE_LIMIT).flatten()
    except discord.errors.Forbidden:
       continue
    
    # Loop through messages and count reactions
    for message in messages:
      for reaction in message.reactions:
        current_reaction = str(reaction.emoji)
        if current_reaction in REACTION_LIST or COUNT_ALL_REACTIONS:
          current_user_id = str(message.author.id)
          if current_user_id in reaction_count:
            # User ID is already in our dictionary 
            if current_reaction in reaction_breakdown[current_user_id]:
              # Current reaction already has a value for the current user
              reaction_breakdown[current_user_id][current_reaction] += reaction.count
            else:
              # Current reaction is not being tracked, set it to the current count
              reaction_breakdown[current_user_id][current_reaction] = reaction.count
            # Add to total count 
            reaction_count[current_user_id] += reaction.count
          else:
            # User is not being tracked yet, add user and current reaction count
            reaction_breakdown[current_user_id] = {current_reaction : reaction.count}
            # Initialize key for total count
            reaction_count[current_user_id] = reaction.count
  
  # Get the top n users with the most combined reactions
  top_users = Counter(reaction_count).most_common(3)

  full_message = '**' + MESSAGE_HEADER + '**\n\n'

  message_end_text = ''

  # Loop through top users and create message string with reaction breakdown
  for user in top_users:
    user_reaction_breakdown = reaction_breakdown[user[0]]

    # Get the string that allows you to @ mention the user
    user_reference = await client.fetch_user(user[0])
    user_mention_str = user_reference.mention

    user_message = user_mention_str + ' with'

    for reaction, count in user_reaction_breakdown.items():
      user_message += ' ' + str(count) + ' ' + reaction + ' reaction' + ('s' if count > 1 else '') + ','

    # Remove trailing comma
    user_message = user_message[:-1]
    # Append to full message
    full_message += user_message + '\n'

  if len(top_users) > 0:
    if top_users[0][1] > REACTION_THRESHOLD and MESSAGE_ABOVE_THRESHOLD:
      message_end_text = MESSAGE_ABOVE_THRESHOLD.replace('_user_mention_', user_mention_str)
    elif top_users[0][1] < REACTION_THRESHOLD and MESSAGE_BELOW_THRESHOLD:
      message_end_text = MESSAGE_BELOW_THRESHOLD

    full_message += '\n' + message_end_text

    channel_to_post = discord.utils.get(guild.channels, name=CHANNEL_TO_POST_IN)
    await channel_to_post.send(full_message)

    print('Message sent')

  else:
    print('No users found with reactions in specified channels')
  

client.run(TOKEN)