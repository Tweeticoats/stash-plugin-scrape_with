#from stash_interface import StashInterface
import requests
import sys
import json


class scrape_with:
    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "DNT": "1"
    }

    def __init__(self, url):
        self.url = url

    def __prefix(self,levelChar):
        startLevelChar = b'\x01'
        endLevelChar = b'\x02'

        ret = startLevelChar + levelChar + endLevelChar
        return ret.decode()

    def __log(self,levelChar, s):
        if levelChar == "":
            return

        print(self.__prefix(levelChar) + s + "\n", file=sys.stderr, flush=True)

    def trace(self,s):
        self.__log(b't', s)

    def debug(self,s):
        self.__log(b'd', s)

    def info(self,s):
        self.__log(b'i', s)

    def warning(self,s):
        self.__log(b'w', s)

    def error(self,s):
        self.__log(b'e', s)

    def progress(self,p):
        progress = min(max(0, p), 1)
        self.__log(b'p', str(progress))

    def __callGraphQL(self, query, variables=None):
        json = {}
        json['query'] = query
        if variables != None:
            json['variables'] = variables

        # handle cookies
        response = requests.post(self.url, json=json, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("error", None):
                for error in result["error"]["errors"]:
                    raise Exception("GraphQL error: {}".format(error))
            if result.get("data", None):
                return result.get("data")
        else:
            raise Exception(
                "GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(response.status_code, response.content,
                                                                                query, variables))

    def listTags(self):
            query = """
    query {
      allTags {
        id
        name
      }
    }"""

            result = self.__callGraphQL(query)
            return result["allTags"]

    def findTagIdWithName(self, name):
        query = """
query {
  allTags {
    id
    name
  }
}
        """

        result = self.__callGraphQL(query)

        for tag in result["allTags"]:
            if tag["name"] == name:
                return tag["id"]
        return None


    def createTagWithName(self, name):
        query = """
mutation tagCreate($input:TagCreateInput!) {
  tagCreate(input: $input){
    id       
  }
}
"""
        variables = {'input': {
            'name': name
        }}

        result = self.__callGraphQL(query, variables)
        return result["tagCreate"]["id"]

    def destroyTag(self, id):
        query = """
mutation tagDestroy($input: TagDestroyInput!) {
  tagDestroy(input: $input)
}
"""
        variables = {'input': {
            'id': id
        }}
        self.__callGraphQL(query, variables)

    def findRandomSceneId(self):
        query = """
query findScenes($filter: FindFilterType!) {
  findScenes(filter: $filter) {
    count
    scenes {
      id
      tags {
        id
      }
    }
  }
}
"""

        variables = {'filter': {
            'per_page': 1,
            'sort': 'random'
        }}

        result = self.__callGraphQL(query, variables)

        if result["findScenes"]["count"] == 0:
            return None

        return result["findScenes"]["scenes"][0]

    def updateScene(self, sceneData):
        query = """
mutation sceneUpdate($input:SceneUpdateInput!) {
  sceneUpdate(input: $input) {
    id
  }
}
"""
        variables = {'input': sceneData}

        self.__callGraphQL(query, variables)

    def list_scrapers(self, type):
        query = """
        query listSceneScrapers {
  listSceneScrapers {
    id
    name
    scene{
      supported_scrapes
    }
  }
}"""
        ret = []
        result = self.__callGraphQL(query)
        for r in result["listSceneScrapers"]:
            if type in r["scene"]["supported_scrapes"]:
                ret.append(r["id"])
        return ret

    def get_scenes_with_tag(self, tag):
        tagID = self.findTagIdWithName(tag)
        query = """query findScenes($scene_filter: SceneFilterType!) {
  findScenes(scene_filter: $scene_filter filter: {per_page: -1}) {
    count
    scenes {
      id
      checksum
      oshash
      title
      details
      url
      date
      rating
      organized
      o_counter
      path
      file {
        size
        duration
        video_codec
        audio_codec
        width
        height
        framerate
        bitrate
      }
      galleries {
        id
        checksum
        path
        title
        url
        date
        details
        rating
        organized
        studio {
          id
          name
          url
        }
        image_count
        tags {
          id
          name
          image_path
          scene_count
        }
      }
      performers {
        id
        name
        gender
        url
        twitter
        instagram
        birthdate
        ethnicity
        country
        eye_color
        country
        height
        measurements
        fake_tits
        career_length
        tattoos
        piercings
        aliases
      }
      studio{
        id
        name
        url
        stash_ids{
          endpoint
          stash_id
        }
      }
      stash_ids{
        endpoint
        stash_id
      }
    }
  }
}"""

        variables = {"scene_filter": {"tags": {"value": [tagID], "modifier": "INCLUDES"}}}
        result = self.__callGraphQL(query, variables)
        return result["findScenes"]["scenes"]

    def scrapeScene(self, scraper, scene):
        query = """query ScrapeScene($scraper_id: ID!, $scene: SceneUpdateInput!) {
  scrapeScene(scraper_id: $scraper_id, scene: $scene) {
    title
    details
    url
    date
    image
    file{
      size
      duration
      video_codec
      audio_codec
      width
      height
      framerate
      bitrate
    }
    studio{
      stored_id
      name
      url
      remote_site_id
    }
    tags{
      stored_id
      name
    }
    performers{
      stored_id
      name
      gender
      url
      twitter
      instagram
      birthdate
      ethnicity
      country
      eye_color
      country
      height
      measurements
      fake_tits
      career_length
      tattoos
      piercings
      aliases
      remote_site_id
      images
    }
    movies{
      stored_id
      name
      aliases
        duration
      date
      rating
      director
      synopsis
      url
    }
    remote_site_id
    duration
    fingerprints{
      algorithm
      hash
      duration
    }
    __typename
  }
}"""
        variables = {"scraper_id": scraper,
                     "scene": {"title": scene["title"], "date": scene["date"], "details": scene["details"],
                               "gallery_ids": [], "id": scene["id"], "movies": None, "performer_ids": [],
                               "rating": scene["rating"], "stash_ids": scene["stash_ids"], "studio_id": None,
                               "tag_ids": None, "url": scene["url"]}}
        result = self.__callGraphQL(query, variables)
        return result["scrapeScene"]

    def findStudioIdWithName(self, name):
        query = """
query {
  allStudios {
    id
    name
  }
}
        """
        result = self.__callGraphQL(query)

        for tag in result["allStudios"]:
            if tag["name"] == name:
                return tag["id"]
        return None

    def findPerformersByName(self, name):
        query = """query FindPerformers(
  $filter: FindFilterType
  $performer_filter: PerformerFilterType
) {
  findPerformers(filter: $filter, performer_filter: $performer_filter) {
    count
    performers {
      ...PerformerData
      __typename
    }
    __typename
  }
}
fragment PerformerData on Performer {
  id
  checksum
  name
  url
  gender
  twitter
  instagram
  birthdate
  ethnicity
  country
  eye_color
  height
  measurements
  fake_tits
  career_length
  tattoos
  piercings
  aliases
  favorite
  image_path
  scene_count
  stash_ids {
    stash_id
    endpoint
    __typename
  }
  __typename
}"""

        variables = {
            "filter":
                {
                    "q": name,
                    "page": 1,
                    "per_page": 100,
                    "sort": "name",
                    "direction": "ASC"
                },
            "performer_filter": {}
        }
        result = self.__callGraphQL(query, variables)
        return result["findPerformers"]["performers"]

    def findPerformer(self, name):
        for performer in self.findPerformersByName(name):
            self.debug("finding performer: "+name+ str(performer["name"]))
            if performer["name"].lower() == name.lower():
                self.debug("Found performer")
                return performer
            if "aliases" in performer:
                if performer["aliases"] == name:
                    return performer
        return None

    def createPerformer(self, performer):
        query = """
            mutation performerCreate($input:PerformerCreateInput!) {
              performerCreate(input: $input){
                id 
              }
            }
            """
        new_performer = {}
        if "name" in performer:
            new_performer["name"] = performer["name"]
        if "url" in performer:
            new_performer["url"] = performer["url"]
        else:
            new_performer["url"] = None
        if "gender" in performer:
            new_performer["gender"] = performer["gender"]
        else:
            new_performer["gender"] = None
        if "birthdate" in performer:
            new_performer["birthdate"] = None
        else:
            new_performer["birthdate"] = None
        if "ethnicity" in performer:
            new_performer["ethnicity"] = performer["ethnicity"]
        else:
            new_performer["country"] = None
        if "ethnicity" in performer:
            new_performer["country"] = performer["country"]
        else:
            new_performer["country"] = None
        if "ethnicity" in performer:
            new_performer["eye_color"] = performer["eye_color"]
        else:
            new_performer["height"] = None

        if "height" in performer:
            new_performer["height"] = performer["height"]
        else:
            new_performer["height"] = None
        if "measurements" in performer:
            new_performer["measurements"] = performer["measurements"]
        else:
            new_performer["measurements"] = None

        if "fake_tits" in performer:
            new_performer["fake_tits"] = performer["fake_tits"]
        else:
            new_performer["fake_tits"] = None
        if "career_length" in performer:
            new_performer["career_length"] = performer["career_length"]
        else:
            new_performer["career_length"] = None

        if "tattoos" in performer:
            new_performer["tattoos"] = performer["tattoos"]
        else:
            new_performer["tattoos"] = None
        if "piercings" in performer:
            new_performer["piercings"] = performer["piercings"]
        else:
            new_performer["piercings"] = None
        if "aliases" in performer:
            new_performer["aliases"] = performer["aliases"]
        else:
            new_performer["aliases"] = None

        if "twitter" in performer:
            new_performer["twitter"] = performer["twitter"]
        else:
            new_performer["twitter"] = None
        if "instagram" in performer:
            new_performer["instagram"] = performer["instagram"]
        else:
            new_performer["instagram"] = None
        if "favorite" in performer:
            new_performer["favorite"] = performer["favorite"]
        else:
            performer["favorite"] = None
        if "image" in performer:
            new_performer["image"] = performer["image"]
        elif "images" in performer:
            if performer["images"] is not None:
                if len(performer["images"]) > 0:
                    new_performer["image"] = performer["images"][0]
                else:
                    new_performer["image"] = None
            else:
                new_performer["image"] = None
        else:
            performer["image"] = None
        if "stash_ids" in performer:
            new_performer["stash_ids"] = performer["stash_ids"]
        else:
            new_performer["stash_ids"] = []

        variables = {'input': new_performer}

        result = self.__callGraphQL(query, variables)
        return result["performerCreate"]




    def setup_tags(self):
        scrapers=self.list_scrapers('FRAGMENT')
        for s in scrapers:
            tagName='scrape_with_'+s
            tagID = self.findTagIdWithName(tagName)
            if tagID == None:
                    tagID = self.createTagWithName(tagName)
                    self.debug("adding tag "+tagName)
            else:
                self.debug("tag exists, "+tagName)


    def update_with_tag(self,tag):

        scenes=self.get_scenes_with_tag(tag)
        #get rid of scrape_with_
        scraper=tag[12:]
        for s in scenes:

            self.info("running scraper on scene: "+s["id"] +" title: "+ s["title"])
            res=self.scrapeScene(scraper,s)
            if res is None:
                self.info("scraper did not return a result")
                newscene={}
                newscene["id"]=s["id"]
                new_tags=[]
                new_id=self.findTagIdWithName("unscrapable")
                if new_id==None:
                    self.info("creating tag: unscrapable")
                    new_id=self.createTagWithName("unscrapable")
                new_tags.append(new_id)
                newscene["tag_ids"]=new_tags
                self.debug("Saving scene: "+str(s["title"]))
                self.updateScene(newscene)
            else:
                self.info("Scraper returned something " )
                newscene={}
                newscene["id"]=s["id"]
                if "title" in res:
                    newscene["title"]=res["title"]
                if "details" in res:
                    newscene["details"]=res["details"]
                if "url" in res:
                    newscene["url"]=res["url"]
                if "date" in res:
                    newscene["date"]=res["date"]
                if "rating" in res:
                    newscene["rating"]=res["rating"]
                if "organized" in res:
                    newscene["organized"]=res["organized"]
                if "studio" in res:
                    if res["studio"] is None:
                        True
                    elif "stored_id" in res["studio"]:
                            newscene["studio_id"]=res["studio"]["stored_id"]
                    elif "name" in res["studio"]:
                        studio_id=self.findStudioIdWithName(res["studio"]["name"])
                        newscene["studio_id"]=studio_id
                if "image" in res:
                    newscene["cover_image"]=res["image"]
                if "tags" in res:
                    new_tags=[]
                    if res["tags"] is not None:
                        for tag in res["tags"]:
                            if "stored_id" in tag:
                                if tag["stored_id"] is not None:
                                   new_tags.append(tag["stored_id"])
                                elif "name" in tag:
                                    new_id = self.findTagIdWithName(tag["name"])
                                    if new_id == None:
                                        self.trace("creating tag: "+ tag["name"])
                                        new_id = self.createTagWithName(tag["name"])
                                    new_tags.append(new_id)
                            elif "name" in tag:
                                new_id=self.findTagIdWithName(tag["name"])
                                if new_id==None:
                                    self.info("creating tag: "+tag["name"])
                                    new_id=self.createTagWithName(tag["name"])
                                new_tags.append(new_id)
                    newscene["tag_ids"]=new_tags
                if "performers" in res:
                    if res["performers"] is not None:
                        self.debug(str(res["performers"]))
                        performer_list=[]
                        for p in res["performers"]:
                            self.debug(str(p))
                            if "stored_id" in p:
                                if p["stored_id"] != None:
                                    performer_list.append(p["stored_id"])
                                elif "name" in p:
                                    new_performer=self.findPerformer(p["name"])
                                    if new_performer==None:
                                        self.info("Creating a new performer: "+ p["name"])
                                        new_performer=self.createPerformer(p)
                                    performer_list.append(new_performer["id"])
                        newscene["performer_ids"]=performer_list
                self.debug("Saving scene: "+str(newscene["title"]))
                self.updateScene(newscene)

    def update_all_scenes_with_tags(self):
        tags=self.listTags()
        for tag in tags:
            if tag["name"].startswith("scrape_with_"):
                self.info("scraping all scenes with tag: "+str(tag["name"]))
                self.update_with_tag(tag["name"])

    def scrape_performer_list(self,scraper_id,performer):
        query="""query scrapePerformerList($scraper_id: ID!, $performer: String!) {
  scrapePerformerList(scraper_id: $scraper_id, query: $performer) {
    name
    url
    gender
    twitter
    instagram
    birthdate
    ethnicity
    country
    eye_color
    height
    measurements
    fake_tits
    career_length
    tattoos
    piercings
    aliases
    image
    }
}"""

        variables = {'scraper_id': scraper_id,'performer': performer}
        result = self.__callGraphQL(query, variables)
        if result is not None:
            return result["scrapePerformerList"]
        return None

    def scrape_performer(self, scraper_id, performer):
        query = """query scrapePerformer($scraper_id: ID!, $performer: ScrapedPerformerInput!) {
  scrapePerformer(scraper_id: $scraper_id, scraped_performer: $performer) {
    name
    url
    gender
    twitter
    instagram
    birthdate
    ethnicity
    country
    eye_color
    height
    measurements
    fake_tits
    career_length
    tattoos
    piercings
    aliases
    image
    }
}"""
        del performer["image"]
        variables = {'scraper_id': scraper_id, 'performer':performer}
        result = self.__callGraphQL(query, variables)
        return result["scrapePerformer"]

    def listPerformerScrapers(self):
        query="""{
  listPerformerScrapers {
    id
    name
    performer {
      urls
      supported_scrapes
    }
  }
}"""
        result = self.__callGraphQL(query)
        return result["listPerformerScrapers"]

    def allPerformers(self):
        query = """{
  allPerformers {
    id
    checksum
    name
    url
    gender
    twitter
    instagram
    birthdate
    ethnicity
    country
    eye_color
    height
    measurements
    fake_tits
    career_length
    tattoos
    piercings
    aliases
    favorite
    image_path
    scene_count
    stash_ids {
      endpoint
      stash_id
    }
  }
}"""
        result = self.__callGraphQL(query)
        return result["allPerformers"]

    def performer_update(self,performer):
        query="""
mutation performerUpdate($input: PerformerUpdateInput!) {
  performerUpdate(input: $input) {
    id
    checksum
    name
    url
    gender
    twitter
    instagram
    birthdate
    ethnicity
    country
    eye_color
    height
    measurements
    fake_tits
    career_length
    tattoos
    piercings
    aliases
    favorite
    image_path
    scene_count
    stash_ids {
      endpoint
      stash_id
    }
  }
}
"""
        variables = {'input': performer}
        return self.__callGraphQL(query, variables)

    def run_update_performers(self,scraper_preference):
        performers=self.allPerformers()
        index=0
        for p in performers:
            index=index+1
            self.progress(index/len(performers))
            if p["url"] is None:
                self.debug("need to scrape performer "+p["name"])
                found=False
                for scraper in scraper_preference:
                    scraped_list=self.scrape_performer_list(scraper,p["name"].lower())
                    if scraped_list is not None:
                        self.debug("scraping "+p["name"]+" with scraper: "+scraper)
                        for s in scraped_list:
                            if (s["name"]).lower()==(p["name"]).lower() and not found:
                                sp=self.scrape_performer(scraper,s)
                                if sp is not None:
                                    if (sp["name"]).lower()==(p["name"]).lower():
                                        found=True
                                        self.info("Found performer "+sp["name"] +" with scraper: " +scraper)
                                        if sp["name"] is not None:
                                            p["name"]=sp["name"]
                                        if sp["url"] is not None:
                                            p["url"]=sp["url"]
                                        if sp["gender"] is not None:
                                            p["gender"]=sp["gender"].upper()
                                        if sp["twitter"] is not None:
                                            p["twitter"]=sp["twitter"]
                                        if sp["instagram"] is not None:
                                            p["instagram"] = sp["instagram"]
                                        if sp["birthdate"] is not None:
                                            p["birthdate"] = sp["birthdate"]
                                        if sp["ethnicity"] is not None:
                                            p["ethnicity"] = sp["ethnicity"]
                                        if sp["country"] is not None:
                                            p["country"] = sp["country"]
                                        if sp["eye_color"] is not None:
                                            p["eye_color"] = sp["eye_color"]
                                        if sp["height"] is not None:
                                            p["height"] = sp["height"]
                                        if sp["measurements"] is not None:
                                            p["measurements"] = sp["measurements"]
                                        if sp["fake_tits"] is not None:
                                            p["fake_tits"] = sp["fake_tits"]
                                        if sp["career_length"] is not None:
                                            p["career_length"] = sp["career_length"]
                                        if sp["tattoos"] is not None:
                                            p["tattoos"] = sp["tattoos"]
                                        if sp["piercings"] is not None:
                                            p["piercings"] = sp["piercings"]
                                        if sp["aliases"] is not None:
                                            p["aliases"] = sp["aliases"]
                                        if sp["image"] is not None:
                                            p["image"] = sp["image"]
                                else:
                                    self.info("Looking up entry did not return a result entry: " +s["name"])
                if found:
                    del p["image_path"]
                    del p["checksum"]
                    del p["scene_count"]
                    self.info("updating performer "+p["name"])
                    self.debug("===name: "+str(p["name"])+ " url: "+str(p["url"])+" gender "+str(p["gender"]))
                    u=self.performer_update(p)
                    if u is not None:
                        self.info("update succesful!!")

    def run_scraper_performers(self,scraper):
        performers=self.allPerformers()
        index=0
        for p in performers:
            index=index+1
            found = False
            self.progress(index/len(performers))
            scraped_list = self.scrape_performer_list(scraper, p["name"].lower())
            if scraped_list is not None:
                for s in scraped_list:
                    if (s["name"]).lower() == (p["name"]).lower() and not found:
                        sp = self.scrape_performer(scraper, s)
                        if sp is not None:
                            if (sp["name"]).lower() == (p["name"]).lower():
                                found = True
                                self.info("Found performer " + sp["name"] + " with scraper: " + scraper)
                                if sp["name"] is not None:
                                    p["name"] = sp["name"]
                                if sp["url"] is not None:
                                    p["url"] = sp["url"]
                                if sp["gender"] is not None:
                                    p["gender"] = sp["gender"].upper()
                                if sp["twitter"] is not None:
                                    p["twitter"] = sp["twitter"]
                                if sp["instagram"] is not None:
                                    p["instagram"] = sp["instagram"]
                                if sp["birthdate"] is not None:
                                    p["birthdate"] = sp["birthdate"]
                                if sp["ethnicity"] is not None:
                                    p["ethnicity"] = sp["ethnicity"]
                                if sp["country"] is not None:
                                    p["country"] = sp["country"]
                                if sp["eye_color"] is not None:
                                    p["eye_color"] = sp["eye_color"]
                                if sp["height"] is not None:
                                    p["height"] = sp["height"]
                                if sp["measurements"] is not None:
                                    p["measurements"] = sp["measurements"]
                                if sp["fake_tits"] is not None:
                                    p["fake_tits"] = sp["fake_tits"]
                                if sp["career_length"] is not None:
                                    p["career_length"] = sp["career_length"]
                                if sp["tattoos"] is not None:
                                    p["tattoos"] = sp["tattoos"]
                                if sp["piercings"] is not None:
                                    p["piercings"] = sp["piercings"]
                                if sp["aliases"] is not None:
                                    p["aliases"] = sp["aliases"]
                                if sp["image"] is not None:
                                    p["image"] = sp["image"]
                if found:
                    del p["image_path"]
                    del p["checksum"]
                    del p["scene_count"]
                    self.info("updating performer "+p["name"])
                    self.debug("===name: "+str(p["name"])+ " url: "+str(p["url"])+" gender "+str(p["gender"]))
                    u=self.performer_update(p)
                    if u is not None:
                        self.info("update succesful!!")

#scraper_preference=["Iafd","Babepedia","stash-sqlite","performer-image-dir"]
scraper_preference=["Iafd","stash-sqlite","performer-image-dir"]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if len(sys.argv) > 1:
        url = "http://localhost:9999/graphql"
        if len(sys.argv) > 2:
            url = sys.argv[2]

        if sys.argv[1] == "setup":
            client = scrape_with(url)
            client.setup_tags()
        elif sys.argv[1] =="scrape":
            client = scrape_with(url)
            tagName=sys.argv[3]
            client.update_with_tag(tagName)
        elif sys.argv[1] =="scrape_all":
            client = scrape_with(url)
            client.update_all_scenes_with_tags()
        elif sys.argv[1] == "performers":
            client= scrape_with(url)
            client.run_update_performers(scraper_preference)
        elif sys.argv[1] == "runperformers":
            client = scrape_with(url)
            client.run_scraper_performers("performer-image-dir")
        elif sys.argv[1]== "api":
            fragment = json.loads(sys.stdin.read())
            scheme=fragment["server_connection"]["Scheme"]
            port=fragment["server_connection"]["Port"]
            domain="localhost"
            if "Domain" in fragment["server_connection"]:
                domain = fragment["server_connection"]["Domain"]
            if not domain:
                domain='localhost'
            url = scheme + "://" + domain + ":" +str(port) + "/graphql"

            client=scrape_with(url)
            mode=fragment["args"]["mode"]
            client.debug("Mode: "+mode)
            if mode == "setup":
                client.setup_tags()
            elif mode == "scrape_all":
                client.update_all_scenes_with_tags()
            elif mode == "performers":
                client.run_update_performers(scraper_preference)
            elif mode == "performers_imagedir":
                client.run_scraper_performers("performer-image-dir")
    else:
        print("")
