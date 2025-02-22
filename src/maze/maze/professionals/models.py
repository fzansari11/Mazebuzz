from maze import db
from maze.users.models import Helper
import datetime

from sqlalchemy.schema import Sequence
 
prof_table = ['userId','profession','acceptsQandA','acceptsVoice','acceptsVideo','acceptsQandA','aboutMe',
              'backgroundCheck','businessCheck','questionRate', 'voiceRate', 'videoRate', 'freeConsult', 
              'receiveSms', 'readyServe', 'firstFree']

timeslot_table = ['userId','monstart','monend','tuesstart','tuesend','wedstart','wedend',
                  'thursstart','thursend','fristart','friend', 'satstart', 'satend','sunstart','sunend']

cred_table = ['userId', 'worksAt', 'workstartdate', 'workenddate', 'specials',
              'languages','degrees', 'schools', 'courses', 'gradyear', 'jobtitle', 'images']
rating_table = ['userId','numVoiceCalls','numVideoCalls','numQuestionAnswered','num1star',
                'num2star','num3star','num4star','num5star','numMissedAppoints', 'avgRating', 'totalReviews']

'''
port_table = ['userId','aboutMe','websiteUrl','imageUrl1','imageUrl2','imageUrl3','imageUrl4','imageUrl5',
              'videoUrl','linkedinUrl']
campaign_table = ['userId','startDate','endDate','offeredPrice','noOfRequestsPerDay',
                   'availableMonday','availableTuesday','availableWednesday','availableThursday',
                   'availableFriday','availableSaturday','availableSunday'
                   'totalOccupiedMon','totalOccupiedTues','totalOccupiedWed','totalOccupiedThur',
                   'totalOccupiedFri','totalOccupiedSat','totalOccupiedSun']
'''


from sqlalchemy import event
from sqlalchemy import DDL
class Profession(db.Model, Helper):
  __tablename__ = 'profession'
  professionId = db.Column(db.Integer, primary_key = True, autoincrement = True)
  professionName = db.Column(db.String(100), index=True)
  subprofessions = db.Column(db.UnicodeText())
   
  def __init__(self, professionName):
    self.professionName = professionName

class SubProfession(db.Model, Helper):
  __tablename__ = 'subprofession'
  professionId = db.Column(db.Integer, primary_key = True, autoincrement = True)
  professionName = db.Column(db.String(100), index=True)
   
  def __init__(self, professionName):
    self.professionName = professionName

  def after_create(target, connection, **kw):
    connection.execute("ALTER TABLE SubProfession AUTO_INCREMENT = 5001")

event.listen(
    SubProfession.__table__,
    "after_create",
    DDL("ALTER TABLE %(table)s AUTO_INCREMENT = 5001;")
)

class ProfTimeSlots(db.Model, Helper):
  __tablename__ = 'proftimeslots'
  userId = db.Column(db.Integer, primary_key = True)
  monstart = db.Column(db.UnicodeText(), default = None)
  monend = db.Column(db.UnicodeText(), default = None)
  tuesstart = db.Column(db.UnicodeText(), default = None)
  tuesend = db.Column(db.UnicodeText(), default = None)
  wedstart = db.Column(db.UnicodeText(), default = None)
  wedend = db.Column(db.UnicodeText(), default = None)
  thursstart = db.Column(db.UnicodeText(), default = None)
  thursend = db.Column(db.UnicodeText(), default = None)
  fristart = db.Column(db.UnicodeText(), default = None)
  friend = db.Column(db.UnicodeText(), default = None)
  satstart = db.Column(db.UnicodeText(), default = None)
  satend = db.Column(db.UnicodeText(), default = None)
  sunstart = db.Column(db.UnicodeText(), default = None)
  sunend = db.Column(db.UnicodeText(), default = None)
   
  def __init__(self, userId):
    self.userId = userId

class Professionals(db.Model, Helper):
  __tablename__ = 'professionals'
  userId = db.Column(db.Integer, primary_key = True)
  profession = db.Column(db.String(100), index = True)
  subprofession = db.Column(db.String(100), index = True)
  subprofession2 = db.Column(db.String(100), default = None)
  subprofession3 = db.Column(db.String(100), default = None)
  acceptsQandA = db.Column(db.Boolean, default = True)
  acceptsVoice = db.Column(db.Boolean, default = True)
  acceptsVideo = db.Column(db.Boolean, default = True)
  isVerified =  db.Column(db.Boolean, default = False)
  readyServe = db.Column(db.Boolean, default = False)
  freeConsult = db.Column(db.Boolean, default = False)
  firstFree = db.Column(db.Boolean, default = False)
  voiceRate = db.Column(db.Float, default =0)
  videoRate = db.Column(db.Float, default =0)
  questionRate = db.Column(db.Float, default =0)
  backgroundCheck = db.Column(db.Boolean, default = False)
  businessCheck = db.Column(db.Boolean, default = False)
  aboutMe = db.Column(db.UnicodeText(), default = u'')
  receiveSms = db.Column(db.Boolean, default = False)
  mazeId = db.Column(db.String(256), index = True)
  balance = db.Column(db.Float, default =0)
  business = db.Column(db.Boolean, default =False)
  mazeprice = db.Column(db.Boolean, default =False)
  verification = db.Column(db.Integer, default =0)
   
  def __init__(self, userId, profession, subprofession=None, subprofession2=None, subprofession3=None, \
               business = False):
    self.userId = userId
    self.profession = profession
    self.subprofession = subprofession
    self.subprofession2 = subprofession2
    self.subprofession3 = subprofession3
    self.business = business


class Credentials(db.Model, Helper):
  __tablename__ = 'credentials'
  userId = db.Column(db.Integer, primary_key = True)
  worksAt = db.Column(db.String(1000), default = '')
  workstartdate = db.Column(db.String(1000), default = '')
  workenddate = db.Column(db.String(1000), default = '')
  specials = db.Column(db.String(1000), default = '')
  languages = db.Column(db.String(1000), default = '')
  degrees = db.Column(db.String(1000), default = '')
  schools = db.Column(db.String(1000), default = '')
  courses = db.Column(db.String(1000), default = '')
  gradyear = db.Column(db.String(1000), default = '')
  jobtitle = db.Column(db.String(1000), default = '')
  images = db.Column(db.UnicodeText(), default = u'')

  def __init__(self, userId):
    self.userId = userId

class ProfessionalRatings(db.Model, Helper):
  __tablename__ = 'professionalRatings'
  userId = db.Column(db.Integer, primary_key = True)
  profession = db.Column(db.String(100), index = True)
  subprofession = db.Column(db.String(100), index=True)
  numVoiceCalls = db.Column(db.Integer, default = 0)
  numVideoCalls = db.Column(db.Integer, default = 0)
  numQuestionAnswered = db.Column(db.Integer, default = 0)
  num1star = db.Column(db.Integer, default = 0)
  num2star = db.Column(db.Integer, default = 0)
  num3star = db.Column(db.Integer, default = 0)
  num4star = db.Column(db.Integer, default = 0)
  num5star = db.Column(db.Integer, default = 0)
  avgRating = db.Column(db.Float, default = 0)
  totalReviews = db.Column(db.Float, default = 0)
  numMissedAppoints = db.Column(db.Integer, default = 0)
   
  def __init__(self, userId, profession, subprofession = None):
    self.userId = userId
    self.profession = profession
    self.subprofession = subprofession

''' All keyword related tables '''
class ProfHasKeywords(db.Model, Helper):
  __tablename__ = 'profhaskeywords'
  userId = db.Column(db.Integer, primary_key = True)
  keyword = db.Column(db.String(100), primary_key = True)
   
  def __init__(self, userId, keyword):
    self.userId = userId
    self.keyword = keyword

class ExactKeywordsProf(db.Model, Helper):
  __tablename__ = 'exactkeywordsprof'
  keyword = db.Column(db.String(100), primary_key = True)
  userId = db.Column(db.Integer, default = 0, primary_key = True)
  profession = db.Column(db.String(100), index=True) 
  subprofession = db.Column(db.String(100))

  def __init__(self, keyword, userId, profession):
    self.keyword = keyword
    self.userId = userId 
    self.profession = profession

class ApproxKeywordsProf(db.Model, Helper):
  __tablename__ = 'approxkeywordsprof'
  keyword = db.Column(db.String(100),  primary_key = True)
  userId = db.Column(db.Integer, default = 0, primary_key = True)
  profession = db.Column(db.String(100), index=True)
  subprofession = db.Column(db.String(100))
   
  def __init__(self, keyword, userId, profession):
    self.keyword = keyword
    self.userId = userId
    self.profession = profession

class Keywords(db.Model, Helper):
  __tablename__ = 'keywords'
  keyword = db.Column(db.String(100),  primary_key = True)
  prof = db.Column(db.Boolean, default = False)
   
  def __init__(self, keyword, prof=False):
    self.keyword = keyword
    self.prof = prof

'''/*************** SERVICES  **********************/'''
'''
class Service(db.Model, Helper):
  __tablename__ = 'service'
  serviceId = db.Column(db.Integer,  primary_key = True, autoincrement = True)
  serviceName = db.Column(db.String(100))
   
  def __init__(self, serviceName):
    self.serviceName = serviceName


class ProfessionHasService(db.Model, Helper):
  __tablename__ = 'professionhasservice'
  professionId = db.Column(db.Integer, primary_key = True)
  serviceId = db.Column(db.Integer, default =0, primary_key = True)
   
  def __init__(self, professionId, serviceId):
    self.professionId = professionId
    self.serviceId = serviceId
'''

'''**** OFFER DETAILS ****'''
'''class Offer(db.Model, Helper):
  __tablename__ = 'offer'
  offerId = db.Column(db.Integer, primary_key = True, autoincrement = True)
  title = db.Column(db.String(100))
  price = db.Column(db.Integer)
  details = db.Column(db.UnicodeText())
  image1 = db.Column(db.String(256), default = '')
  image2 = db.Column(db.String(256), default = '')
  image3 = db.Column(db.String(256), default = '')
  video = db.Column(db.String(256), default = '')
   
  def __init__(self, title, price, details, image1='', image2='', image3='', video=''):
    self.title = title
    self.price = price
    self.details = details
    self.image1 = image1
    self.image2 = image2
    self.image3 = image3

class ProfessionalFreeConsult(db.Model, Helper):
  __tablename__ = 'professionalfreeconsult'
  professionalId = db.Column(db.Integer, primary_key = True)
  userId = db.Column(db.Integer, default =0, primary_key = True)
   
  def __init__(self, professionalId, userId):
    self.professionalId = professionalId
    self.userId = userId

class ProfessionalHasOffer(db.Model, Helper):
  __tablename__ = 'professionalhasoffer'
  userId = db.Column(db.Integer, primary_key = True)
  offerId = db.Column(db.Integer, default =0, primary_key = True)
   
  def __init__(self, userId, offerId):
    self.userId = userId
    self.offerId = offerId

class ServiceHasOffer(db.Model, Helper):
  __tablename__ = 'servicehasoffer'
  serviceId = db.Column(db.Integer, primary_key = True)
  offerId = db.Column(db.Integer, default =0, primary_key = True)
   
  def __init__(self, serviceId, offerId):
    self.serviceId = serviceId
    self.offerId = offerId
'''


''''******* KEYWORDS ******'''''
'''class ExactKeywords(db.Model, Helper):
  __tablename__ = 'exactkeywords'
  keyword = db.Column(db.String(100), primary_key = True)
  offerId = db.Column(db.Integer, default = 0, primary_key = True)
   
  def __init__(self, keyword, offerId):
    self.keyword = keyword
    self.offerId = offerId

class ApproxKeywords(db.Model, Helper):
  __tablename__ = 'approxkeywords'
  keyword = db.Column(db.String(100),  primary_key = True)
  offerId = db.Column(db.Integer, default = 0, primary_key = True)
   
  def __init__(self, keyword, offerId):
    self.keyword = keyword
    self.offerId = offerId

class Portfolio(db.Model, Helper):
  __tablename__ = 'portfolio'
  userId = db.Column(db.Integer, primary_key = True)
  aboutMe = db.Column(db.UnicodeText(), default = u'')
  websiteUrl = db.Column(db.String(100), default = '')
  images = db.Column(db.UnicodeText(), default = '')
  videoUrl = db.Column(db.String(100), default = '')
  linkedinUrl = db.Column(db.String(256), default = '')
   
  def __init__(self, userId):
    self.userId = userId

class Campaign(db.Model, Helper):
  __tablename__ = 'campaign'
  userId = db.Column(db.Integer, primary_key = True)
  professionId = db.Column(db.Integer, default =0)
  startDate = db.Column(db.DateTime, default = datetime.datetime.utcnow)
  endDate = db.Column(db.DateTime, default = datetime.datetime.utcnow)
  offeredPrice = db.Column(db.Integer, default = 0)
  noOfRequestsPerDay = db.Column(db.Boolean, default = False)
  availableMonday = db.Column(db.Boolean, default = False)
  availableTuesday = db.Column(db.Boolean, default = False)
  availableWednesday = db.Column(db.Boolean, default = False)
  availableThursday = db.Column(db.Boolean, default = False)
  availableFriday = db.Column(db.Boolean, default = False)
  availableSaturday = db.Column(db.Boolean, default = False)
  availableSunday = db.Column(db.Boolean, default = False)
  totalOccupiedMon = db.Column(db.String(100), default = '')
  totalOccupiedTue = db.Column(db.String(100), default = '')
  totalOccupiedWed = db.Column(db.String(100), default = '')
  totalOccupiedThur = db.Column(db.String(100), default = '')
  totalOccupiedFri = db.Column(db.String(100), default = '')
  totalOccupiedSat = db.Column(db.String(100), default = '')
  totalOccupiedSun = db.Column(db.String(100), default = '')
   
  def __init__(self, userId, professionId):
    self.userId = userId
    self.professionId = professionId'''
