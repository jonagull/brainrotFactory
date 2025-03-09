import praw
import json
from datetime import datetime

# Initialize Reddit instance
reddit = praw.Reddit(
    client_id="rtFPl_S0fmuRxVM1vIF_-g",         # This is your client_id
    client_secret="kkdb0G2lUK-t5gm8EjAMvJ9kl10whA",  # This is your secret
    user_agent="script:brainrotfactory:v1.0 (by /u/boientheboi)"  # Replace YOUR_REDDIT_USERNAME with your actual Reddit username
)

# kkdb0G2lUK-t5gm8EjAMvJ9kl10whA SECRET

# print(reddit.user.me())  # Should print "None" for script-only apps

def get_top_posts(subreddit_name, limit=10, max_length=10000):
    """
    Get top posts from a specified subreddit and save to JSON
    max_length: maximum number of characters allowed in a story (default 10000)
    """
    subreddit = reddit.subreddit(subreddit_name)
    top_posts = subreddit.top(limit=limit, time_filter="week")
    
    stories = []
    skipped = 0
    
    for post in top_posts:
        # Skip if content is too long
        if post.is_self and len(post.selftext) > max_length:
            print(f"\nSkipped (too long): {post.title}")
            print(f"Length: {len(post.selftext)} characters")
            skipped += 1
            continue
            
        story_data = {
            "title": post.title,
            "author": str(post.author),  # Convert author to string in case account is deleted
            "score": post.score,
            "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
            "url": post.url,
            "content": post.selftext if post.is_self else "",
        }
        stories.append(story_data)
        
        # Print info about saved story
        print(f"\nSaved: {post.title}")
        if post.is_self:
            print(f"Length: {len(post.selftext)} characters")
        print("-" * 50)
    
    # Save to JSON file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"creepypasta_stories_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=4, ensure_ascii=False)
    
    print(f"\nSaved {len(stories)} stories to {filename}")
    print(f"Skipped {skipped} stories that were too long")

if __name__ == "__main__":
    # Example usage
    # subreddit_name = "AskReddit"  # Change this to any subreddit you want
    subreddit_name = "creepypasta"  # Change this to any subreddit you want
    get_top_posts(
        subreddit_name=subreddit_name,
        limit=10,           # Number of posts to fetch
        max_length=10000    # Maximum characters (adjust this as needed)
    )
