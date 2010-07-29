import re, string
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

BM_PREFIX        = '/video/billmoyers'
BM_ROOT          = 'http://www.pbs.org'
BM_ARCHIVES      = 'http://www.pbs.org/moyers/journal/archives/archives.php?start=480'
BM_TOPICS        = 'http://www.pbs.org/moyers/journal/archives/topics.php'
BM_TOPICS_SEARCH = 'http://www.pbs.org/moyers/journal/archives/results.php?topics[]=%s&search=Search'

BM_RSS_FEED      = 'http://feeds.pbs.org/pbs/moyers/journal-video'
BM_RSS_NS        = {'media':'http://search.yahoo.com/mrss/', 'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}

CACHE_INTERVAL = 3600*8

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(BM_PREFIX, MainMenu, 'Bill Moyers Journal', 'icon-default.jpg', 'art-default.jpg')
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.title1 = 'Bill Moyers Journal'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.jpg')
  HTTP.SetCacheTime(CACHE_INTERVAL)

####################################################################################################
def UpdateCache():
  HTTP.Request(BM_RSS_FEED)
  HTTP.Request(BM_ARCHIVES)
  HTTP.Request(BM_TOPICS)
  
####################################################################################################
def MainMenu():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(GetPodcast, title="All Videos")))
  #dir.Append(Function(DirectoryItem(GetRecentVideos, title="Archive")))
  dir.Append(Function(DirectoryItem(GetTopics,       title="By Topic")))
  return dir

####################################################################################################
def GetPodcast(sender):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
  for item in XML.ElementFromURL(BM_RSS_FEED).xpath('//item'):
    title = item.find('title').text
    key = item.find('enclosure').get('url')
    date = Datetime.ParseDate(item.find('pubDate').text).strftime('%a %b %d, %Y')
    summary = item.xpath('itunes:summary', namespaces=BM_RSS_NS)[0].text
    subtitle = date
    #item.xpath('itunes:keywords', namespaces=BM_RSS_NS)[0].text
    
    duration = item.xpath('itunes:duration', namespaces=BM_RSS_NS)[0].text
    duration = [int(i) for i in duration.split(':')]
    duration = (duration[0]*60 + duration[1])*1000
    
    dir.Append(VideoItem(key, title=title, subtitle=subtitle, duration=duration, summary=summary, thumb=R('icon-default.jpg')))
  
  return dir

####################################################################################################
def GetRecentVideos(sender, page=0, url=BM_ARCHIVES):
  dir = MediaContainer(viewGroup='Details', title2='Recent Videos')
  date = ''
  video_url = 'http://www-tc.pbs.org/moyers/journal/%s/images/vid%s_big.jpg'
  
  for div in XML.ElementFromURL(url, True, errors='ignore').xpath('//div'):
    id = div.get('id')
    if id == 'date2':
      date = div.text
      if date == 'January 18, 2008':
        video_url = 'http://www-tc.pbs.org/moyers/journal/%s/images/vidbig%s.jpg'
      elif date == 'December 7, 2007':
        video_url = 'http://www-tc.pbs.org/moyers/journal/images/bmj_big.jpg'
      
    if id == 'entry':
      key = None
      thumb = None
      
      for mm in div.xpath('div[@id="multimedia"]/a'):
        if mm.get('href').find('watch') != -1:
          key = mm.get('href')
          match = re.search("http://www.pbs.org/moyers/journal/(.*)/watch(.*).html", key)
          thumb_key = match.group(1)
          video_index = match.group(2)
          if len(video_index) == 0:
            video_index = "1"
            
          if video_url.find('%') != -1:
            thumb = video_url % (thumb_key, video_index)
          else:
            thumb = video_url
          
          break
        
      if key:
        title = div.find('a').text
        subtitle = date
        summary = [a for a in div.itertext()][1]
        dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=subtitle, summary=summary, thumb=thumb), url=key))
  
  return dir
  
####################################################################################################
def GetTopics(sender):
  dir = MediaContainer(title2='Topics')
  
  values = []
  for topic in XML.ElementFromURL(BM_TOPICS, True).xpath('//input[@type="checkbox"]'):
    values.append(topic.get('value'))
    
  values.sort()
  for value in values:
    url = BM_TOPICS_SEARCH % value.replace(' ','+')
    dir.Append(Function(DirectoryItem(GetRecentVideos, title=string.capwords(value)), url=url))
  
  return dir

####################################################################################################
def Search(sender, query, page=1):
  return GetTopicMenu(sender, url=BM_SEARCH+query.replace(' ','+'))

####################################################################################################
def PlayVideo(sender, url):
  page = HTTP.Request(url)
  match = re.search("addVariable\(\"file\", \"(.*flv)\"\);", page)
  video_url = BM_ROOT + match.group(1)
  return Redirect(video_url)
