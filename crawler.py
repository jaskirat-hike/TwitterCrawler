# -*- coding: utf-8 -*-

import time
import csv
import string
import requests
import tweepy

class TwitterAPI(object):
    def __init__(self):
        self.users_to_crawl = []
        self.crawled_users = {}
        self.api = self.get_api()
        self.blacklist = self.load_blacklisted_urls()

    def get_api(self):
        consumer_key = "yx0SU3mA2IEj2R5Q11MsexdMT"
        consumer_secret = "xH70Wy8E77owxZufAZc4k9Beh49HsAS8n82W70MOXMDsbnBTwo"
        access_token = "3059873208-AkhBa42pFXfsc1sGwCbiUUvvq9oGP8hlA74JopX"
        access_secret = "Ay3F3JG6AFnd73TunqIefFAguqMDgQUyIt3CYjpI7ixCT"

        # authenticate using tweepy
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_secret)
        api = tweepy.API(auth)
        return api

    def load_blacklisted_urls(self):
        file_name = "blacklisted_urls.txt"
        urls = open(file_name).read().split("\r\n")
        blacklist = {}
        for url in urls:
            if blacklist.get(url, -1) == -1:
                blacklist[url] = 1
        return blacklist

    def begin_sleep_sequence(self):
        print
        print "~" * 20,
        print "Sleeping",
        print "~" * 20
        print
        time.sleep(300)
        print "*" * 20,
        print "Waking Up",
        print "*" * 20,
        print
    
    def get_user(self, user):
        try:
            return self.api.get_user(user)
        except tweepy.error.TweepError as err:
            if err[0][0]['code'] == 88:
                self.begin_sleep_sequence()
                return self.get_user(user)

    def get_intersection_users(self, followers, following):
        # returns a list of users ids in intersection
        # of followers and following
        intersection = []
        user_map = {}

        for user in followers:
            if user_map.get(user, 0) == 0:
                user_map[user] = 1

        # calculate any duplicate users
        for user in following:
            if user_map.get(user, 0) == 1:
                intersection.append(user)

        return intersection

    def get_followers_list(self, user_id):
        # returns list of INTs (twitter ids)
        try:
            return self.api.followers_ids(user_id)
        except tweepy.error.TweepError as err:
            if err[0][0]['code'] == 88:
                self.begin_sleep_sequence()
                return self.get_followers_list(user_id)


    def get_following_list(self, user_id):
        # returns list of INTs (twitter ids)
        try:
            return self.api.friends_ids(user_id)
        except tweepy.error.TweepError as err:
            if err[0][0]['code'] == 88:
                self.begin_sleep_sequence()
                return self.get_following_list(user_id)

    def add_following(self, following_list):
        # followers: list of user ids
        for user in following_list:
            if self.crawled_users.get(user, -1) == -1:
                self.users_to_crawl.append(user)

    def get_tweets(self, user_id):
        try:
            return self.api.user_timeline(user_id, count = 100)
        except tweepy.error.TweepError as err:
            if err[0][0]['code'] == 88:
                self.begin_sleep_sequence()
                return self.get_tweets(user_id)

    def extract_user_details(self, user):
        # extract required details from user object
        # and write to FILE 1
        data = []
        data.append(str(user.id))
        data.append(user.screen_name.encode('utf-8'))
        data.append(user.description.encode('utf-8'))
        data.append(user.name.encode('utf-8'))
        data.append(user.location.encode('utf-8'))
        data.append(str(user.statuses_count))
        data.append(str(user.followers_count))
        data.append(str(user.friends_count))
        data.append(str(user.created_at))

        # write csv row to file
        csvfile = open('user_info.csv', 'a')
        writer = csv.writer(csvfile, quoting = csv.QUOTE_ALL)
        writer.writerow(data)
        csvfile.close()

    def get_full_url(self, short_url):
        try:
            full_url = requests.head(short_url).headers['location']
            slashes = False
            if 'http://www' not in full_url or 'https://www' not in full_url:
                domain_start = full_url.find('//')
                slashes = True
            else:
                domain_start = full_url.find('.')

            if slashes:
                domain_end = full_url.find('/', domain_start + 2)
            else:
                domain_end = full_url.find('/', domain_start)
            
            if domain_end == -1:
                domain_end = full_url.find(" ", domain_start)

            if domain_end == -1:
                if slashes:
                    return full_url[domain_start + 2:]
                else:
                    return full_url[domain_start + 1:]
            else:
                if slashes:
                    return full_url[domain_start + 2: domain_end]
                else:
                    return full_url[domain_start + 1: domain_end]
        except:
            return ""

    def check_if_reply(self, tweet):
        # returns 1 if tweet contains `@`, else 0
        for char in tweet:
            if char == '@':
                return 1
        return 0

    def count_hashtags(self, tweet):
        # returns number of `#` in tweet
        count = 0
        for char in tweet:
            if char == '#':
                count += 1
        return count

    def check_url(self, tweet):
        # returns 1 if tweet contains url, else 0
        test_1 = "http://t.co/"
        test_2 = "https://t.co/"

        if test_2 in tweet or test_1 in tweet:
            return 1
        return 0

    def get_user_id(self, twitter_handle):
        try:
            user = self.api.get_user(twitter_handle)
            return user.id
        except tweepy.error.TweepError as err:
            if err[0][0]['code'] == 88:
                self.begin_sleep_sequence()
                return self.get_user_id(twitter_handle)
        except:
            return -1

    def check_intersecting_user_reply(self, tweet, intersection):
        # returns 1 if the user being replied to
        # belongs to the intersecting user list, 0 otherwise
        handle = ""
        reply_start = tweet.find('@')
        if reply_start == -1:
            return 0

        test_string = tweet[reply_start + 1:]
        test_string = test_string.lower()
        for char in test_string:
            if char in string.lowercase or char in string.digits or char == '_':
                # part of twitter handle
                handle += char
            else:
                break

        # get user id (INT) of the twitter handle
        user_id = self.get_user_id(handle)

        # check if twitter handle belongs to intersection
        return int(user_id in intersection)

    def check_spam_url(self, tweet):
        # returns 1 if url is blacklisted, else 0
        # extract url from tweet
        test_1 = "http://t.co/"
        test_2 = "https://t.co/"

        if test_1 in tweet:
            test_string = test_1
        elif test_2 in tweet:
            test_string = test_2
        else:
            return 0

        start_index = tweet.find(test_string)
        short_url = tweet[start_index: start_index + len(test_string) + 10]


        # get domain name
        domain = self.get_full_url(short_url)
        if domain == "":
            return 0
        elif 'www.' in domain:
            domain = domain.strip('www.')

        # match with blacklisted urls
        return self.blacklist.get(domain, 0)

    def extract_hashtags(self, tweet):
        hashtag_list = []

        test_string = tweet.lower()
        tag = ""

        while True:
            start_index = test_string.find('#')
            if start_index == -1:
                break

            test_string = test_string[start_index + 1:]
            
            counter = 0
            for char in test_string:
                counter += 1
                if char in string.lowercase or char in string.digits or char == '_':
                    tag += char
                else:
                    break

            # add the extracted hashtag to list
            hashtag_list.append(tag)
            tag = ""
            test_string = test_string[counter - 1:]

        return hashtag_list

    def extract_tweets(self, tweets, intersection):
        # tweets: list of tweets, made up of Tweet objects
        # write to FILE 2
        
        # open output FILE 2
        csvfile_2 = open('tweets.csv', 'a')
        writer_2 = csv.writer(csvfile_2, quoting = csv.QUOTE_ALL)

        # open output FILE 3
        csvfile_3 = open('processed_tweets.csv', 'a')
        writer_3 = csv.writer(csvfile_3, quoting = csv.QUOTE_ALL)
        
        reply_count = 0
        hashtag_count = 0
        repeated_hashtag_count = 0
        url_tweet_count = 0
        spam_url_tweet_count = 0
        reply_to_intersection = 0
        hashtags_used = {}

        tweets_processed = False

        # read tweets
        for tweet in tweets:
            tweets_processed = True
            data = []
            data.append(str(tweet.author.id))
            data.append(tweet.text.encode('utf-8'))
            data.append(str(tweet.created_at))
            data.append(tweet.source.encode('utf-8'))
            # write data for FILE 2
            writer_2.writerow(data)

            # extract data for FILE 3
            tweet_text = tweet.text.encode('utf-8')
            twitter_id = tweet.author.id

            is_reply = self.check_if_reply(tweet_text)

            if is_reply:
                reply_count += 1
                if len(intersection):
                    reply_to_intersection += self.check_intersecting_user_reply(tweet_text, intersection)

            has_hashtag = self.count_hashtags(tweet_text)
            if has_hashtag:
                hashtag_count += has_hashtag

                for hashtag in self.extract_hashtags(tweet_text):
                    if hashtags_used.get(hashtag, -1) == -1:
                        hashtags_used[hashtag] = 1
                    else:
                        hashtags_used[hashtag] += 1

            url_in_tweet = self.check_url(tweet_text)
            if url_in_tweet > 0:
                url_tweet_count += 1
                spam_url_tweet_count += self.check_spam_url(tweet_text)

        for value in hashtags_used.values():
            if value > 1:
                repeated_hashtag_count += 1

        # structure data for FILE 3
        if tweets_processed:

            data_3 = []
            data_3.append(str(twitter_id))
            data_3.append(str(reply_count))
            data_3.append(str(reply_to_intersection))
            data_3.append(str(hashtag_count))
            data_3.append(str(repeated_hashtag_count))
            data_3.append(str(url_tweet_count))
            data_3.append(str(spam_url_tweet_count))

            # write data for FILE 3
            writer_3.writerow(data_3)

        # close files
        csvfile_2.close()
        csvfile_3.close()

    def process_user(self, user_id, intersection):
        # process user data

        # get user details
        user = self.get_user(user_id)

        # populate user details for FILE 1
        print "Fetching account details...",
        self.extract_user_details(user)
        print "done!"

        # fetch tweets of chosen user
        print "Fetching tweets...",
        tweets = self.get_tweets(user_id)
        print "done!"

        # populate tweets for FILE 2
        print "Processing tweets...",
        self.extract_tweets(tweets, intersection)
        print "done!"

    def crawl(self, seed):
        # begin BFS crawling beginning from a seed user
        seed_user = self.get_user(seed)
        
        # add seed user
        self.users_to_crawl.append(seed_user.id)
        
        # begin BFS
        account_number = 0
        while len(self.crawled_users) < 15 and len(self.users_to_crawl) > 0:
            # extract user from list of users to be crawled
            user_id = self.users_to_crawl.pop(0)

            account_number += 1
            print "Processing account", str(account_number) + "..."

            # get users followed by extracted user
            print "Fetching followed...",
            following_list = self.get_following_list(user_id)
            print "done!"

            # get users following the extracted user
            print "Fetching following...",
            followers_list = self.get_followers_list(user_id)
            print "done!"

            # get the intersection of followers and following
            print "Calculating intersecting accounts...",
            intersecting_users = self.get_intersection_users(following_list, followers_list)
            print "done!"

            # add following list users to users-TO-BE-crawled list
            self.add_following(following_list)

            # process extracted user's data
            self.process_user(user_id, intersecting_users)
            print "Account processed successfully!"
            print "=" * 30
            print

            # add processed user to crawled users list
            self.crawled_users[user_id] = 1

        print "-" * 15,
        print str(account_number), "accounts processed.",
        print "-" * 15


crawler = TwitterAPI()
crawler.crawl('PMOIndia')
