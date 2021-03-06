import praw
from prawcore import PrawcoreException
import time
import json
from threading import Thread

no_flair_removal = """
**Unfortunately, we've had to remove your post.**
___

___
[**Here are our subreddit rules.**](https://www.reddit.com/r/{}/wiki/rules) - If you have any queries about this, you can contact us via [Moderator Mail](https://www.reddit.com/message/compose?to=%2Fr%2F{})."""

class RedditFlairEnforcer:
    def __init__(self):
        self.start_time = time.time()
        self.reddit = self.login()
        print('--- logged in to reddit')

        self.post_storage = []
        self.thread_storage = {}
        print('--- storage initalized')

        for sub in config['reddit']['subreddits']:
            self.thread_storage[sub] = Thread(target=self.get_posts, args=[sub])
            self.thread_storage[sub].start()

        Thread(target=self.check_flair).start()
        print(f'--- {len(self.thread_storage)} threads started and stored')
        print('--- post processing started')

    def login(self):
        return praw.Reddit(
            client_id=config['reddit']['id'],
            client_secret=config['reddit']['secret'],
            user_agent=config['reddit']['agent'],
            username=config['reddit']['username'],
            password=config['reddit']['password']
        )

    def get_posts(self, sub):
        try:
            for post in self.reddit.subreddit(sub).stream.submissions():
                if post.created_utc - self.start_time > 0:
                    self.post_storage.append({'key': post.id, 'sub': sub, 'time': post.created_utc})
        except PrawcoreException as e:
            print(f'exception: {e}')

    def check_flair(self):
        while True:
            try:
                filtered = filter(lambda x: x['time'] + 30 * 60 - time.time() < 0, self.post_storage)

                for data in filtered:
                    post = self.reddit.submission(data['key'])
                    self.post_storage.remove(data)

                    if post.link_flair_text is None or post.link_flair_css_class is None:
                        post.reply(no_flair_removal.format(data['sub'], data['sub'])).mod.distinguish(how='yes', sticky=True)
                        post.mod.remove()
                        post.mod.lock()
                        print(f'post removed (no flair): {post.id} | {time.time()}')
                    else:
                        print(f'all checks passed: {post.id} ({post.subreddit.display_name}, {post.domain}, {post.link_flair_css_class})')

            except PrawcoreException as e:
                print(f'exception: {e}')


if __name__ == '__main__':
    with open('./config.json') as config_file:
        config = json.load(config_file)
    RedditFlairEnforcer()
