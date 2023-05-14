import logging
import os
import telegram
import youtube_dl

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext




# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a command handler for the /start command
def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(f'Hi {user.first_name}! Please send me a YouTube link to download.')

# Define a message handler for messages that contains a YouTube link
def download_video(update: Update, _: CallbackContext) -> None:
    """Download and send the video file to the user"""
    url = update.message.text
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': '%(title)s.%(ext)s',
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
        except youtube_dl.utils.DownloadError as e:
            update.message.reply_text('An error occurred while downloading the video. Please check your link and try again.')
            logger.error(e)
            return

    # Check if the video has both audio and video streams
    streams = info_dict.get('formats', [info_dict])
    if not has_audio_video(streams):
        update.message.reply_text('The video you provided does not have both audio and video streams.')
        return


def build_format_keyboard(streams):
    """Build a list of available video/audio formats for the user to select from"""
    keyboard = []
    for stream in streams:
        if 'video' in stream['acodec']:
            keyboard.append([stream['format_note'] + ' Video'])
        if 'audio' in stream['acodec']:
            keyboard.append([stream['format_note'] + ' Audio'])
    return keyboard
        


from telegram.ext import CallbackContext
context = CallbackContext








# Retrieve the updater object
updater = context.bot



# Define the streams variable
streams = None


# Retrieve the context object
context = updater.dispatcher





# Define the reply markup and info_dict variables before using them
reply_markup = None
info_dict = None

# Send a message to the user to select a video or audio format

if streams:
    reply_markup = telegram.ReplyKeyboardMarkup(build_format_keyboard(streams))
    update = context.update
    update.message.reply_text('Please select a format:', reply_markup=reply_markup)
    

    # Save the video info to a global variable so it can be accessed later
    global video_info
    video_info = info_dict
else:
    update.message.reply_text('No streams found for the provided URL.')

# Define a message handler for the user's selected format
def select_format(update: Update, _: CallbackContext) -> None:
    """Download and send the video or audio file to the user"""
    format_selected = update.message.text
    video_title = video_info['title']

    # Build the options for downloading the video or audio stream
    ydl_opts = {
        'outtmpl': f'{video_title}.%(ext)s',
    }
    if format_selected == 'Audio':
        ydl_opts['format'] = get_audio_format(video_info)
    else:
        ydl_opts['format'] = get_video_format(video_info, format_selected)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            # Download the video or audio stream
            file_path = ydl.download([video_info['webpage_url']])
        except youtube_dl.utils.DownloadError as e:
            update.message.reply_text('An error occurred while downloading the video. Please try again.')
            logger.error(e)
            return

    bot=context.bot
    # Send the video or audio file to the user
    bot.send_document(chat_id=update.message.chat_id, document=open(file_path[0], 'rb'))

    # Clean up the downloaded file
    os.remove(file_path[0])

def has_audio_video(streams):
    def download_audio(update, context):
    # add your code to download the audio stream h
        pass
    
    
    
    """Check if the video has both audio and video streams"""
    has_video = False
    has_audio = False
    for stream in streams:
        if 'video' in update.message.text:
            download_video(update, context)
            has_video = True
        elif 'audio' in update.message.text:
            download_audio(update, context)
            has_audio = True
        if has_video and has_audio:
            return True
    return False



    
    for stream in streams:
        if 'video' in stream['acodec']:
            has_video = True
        if 'audio' in stream['acodec']:
            has_audio = True
    return has_video and has_audio        



def get_video_format(info_dict, format_selected):
    """Get the YouTube DL format code for the selected video format"""
    formats = info_dict.get('formats', [info_dict])
    for f in formats:
        if f.get('format_note', '').lower() == format_selected.lower():
            return f.get('format_id', formats[-1]['format_id'])


def get_audio_format(info_dict):
    """Get the YouTube DL format code for the best audio format"""
    formats = info_dict.get('formats', [info_dict])
    audio_formats = []
    for f in formats:
        if 'audio' in f['acodec']:
            audio_formats.append(f)
    audio_formats = sorted(audio_formats, key=lambda f: f.get('abr', 0), reverse=True)
    return audio_formats[0]['format_id']


def cancel(update: Update, _: CallbackContext) -> None:
    """Cancel the current conversation"""
    update.message.reply_text('Conversation canceled.', reply_markup=telegram.ReplyKeyboardRemove())
    return


def help_command(update: Update, _: CallbackContext) -> None:
    """Display the help message"""
    update.message.reply_text('Send me a YouTube link and I will download the video for you. '
                              'You can select the video or audio format and resolution you want. '
                              'Just type /cancel at any time to cancel the current conversation.')


def main() -> None:
    """Start the bot."""
    # Get the bot token from the environment variable
    bot_token = os.environ.get("BOT_TOKEN")
    if bot_token is None:
        logger.error("Please set the BOT_TOKEN environment variable.")
        return

    # Create the Updater and pass it the bot token
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("cancel", cancel))

    # Register the message handler for YouTube links
    dispatcher.add_handler(MessageHandler(Filters.regex(r'(http|https)://(www\.youtube\.com|youtu\.be)/'), download_video))

    # Register the message handler for video or audio format selection
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^720p$|^480p$|^360p$|^240p$|^144p$|^Audio$'), select_format))

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()

