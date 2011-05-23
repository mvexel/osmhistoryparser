class node(object):
	def __init__(self):
		self._lat = None
		self._lon = None
		self._version = None
		self._user_id = None
		self._user = None
		self._id = None
		self._visible = None
		self._tags = {}
		self._timestamp = None
		self._changeset_id = None
		self._visible = None

	def getlat(self):
		return self._lat
	def setlat(self, value):
		self._lat = float(value)
	def dellat(self):
		del self._lat
	lat = property(getlat, setlat, dellat, "latitude")

	def getlon(self):
		return self._lon
	def setlon(self, value):
		self._lon = float(value)
	def dellon(self):
		del self._lon
	lon = property(getlon, setlon, dellon, "longitude")

	def getversion(self):
		return self._version
	def setversion(self, value):
		self._version = value
	def delversion(self):
		del self._version
	version = property(getversion, setversion, delversion, "version")

	def getuser_id(self):
		return self._user_id
	def setuser_id(self, value):
		self._user_id = value
	def deluser_id(self):
		del self._user_id
	user_id = property(getuser_id, setuser_id, deluser_id, "user id")

	def getuser(self):
		return self._user
	def setuser(self, value):
		self._user = value
	def deluser(self):
		del self._user
	user = property(getuser, setuser, deluser, "user id")

	def getid(self):
		return self._id
	def setid(self, value):
		self._id = value
	def delid(self):
		del self._id
	id = property(getid, setid, delid, "node id")

	def getvisible(self):
		return self._visible
	def setvisible(self, value):
		self._visible = value
	def delvisible(self):
		del self._visible
	visible = property(getvisible, setvisible, delvisible, "visibility")

	@property
	def tags(self):
		"""I'm the 'tag' property."""
		return self._tags

	@tags.setter
	def x(self, key, value):
		self._tag[key] = value

	@x.deleter
	def x(self):
		del self._x

	def gettimestamp(self):
		return self._timestamp
	def settimestamp(self, value):
		self._timestamp = value
	def deltimestamp(self):
		del self._timestamp
	timestamp = property(gettimestamp, settimestamp, deltimestamp, "timestamp")

	def getchangeset_id(self):
		return self._changeset_id
	def setchangeset_id(self, value):
		self._changeset_id = value
	def delchangeset_id(self):
		del self._changeset_id
	changeset_id = property(getchangeset_id, setchangeset_id, delchangeset_id, "changeset_id")

	def getvisible(self):
		return self._visible
	def setvisible(self, value):
		self._visible = value
	def delvisible(self):
		del self._visible
	visible = property(getvisible, setvisible, delvisible, "visible")

class way(object):
	def __init__(self):
		self._version = None
		self._user_id = None
		self._user = None
		self._id = None
		self._visible = None
		self._tags = {}
		self._noderefs = []
		self._timestamp = None
		self._changeset_id = None
		self._visible = None

	def getversion(self):
		return self._version
	def setversion(self, value):
		self._version = value
	def delversion(self):
		del self._version
	version = property(getversion, setversion, delversion, "version")

	def getuser_id(self):
		return self._user_id
	def setuser_id(self, value):
		self._user_id = value
	def deluser_id(self):
		del self._user_id
	user_id = property(getuser_id, setuser_id, deluser_id, "user id")

	def getuser(self):
		return self._user
	def setuser(self, value):
		self._user = value
	def deluser(self):
		del self._user
	user = property(getuser, setuser, deluser, "user id")

	def getid(self):
		return self._id
	def setid(self, value):
		self._id = value
	def delid(self):
		del self._id
	id = property(getid, setid, delid, "node id")

	def getvisible(self):
		return self._visible
	def setvisible(self, value):
		self._visible = value
	def delvisible(self):
		del self._visible
	visible = property(getvisible, setvisible, delvisible, "visibility")

	@property
	def tags(self):
		"""I'm the 'tag' property."""
		return self._tags

	@tags.setter
	def x(self, key, value):
		self._tag[key] = value

	@x.deleter
	def x(self):
		del self._x

	def getnoderefs(self):
		return self._noderefs
	def setnoderefs(self, value):
		self._noderefs = value
	def delnoderefs(self, value):
		del self._noderefs[:]
	noderefs = property(getnoderefs, setnoderefs, delnoderefs, "noderefs")

	def gettimestamp(self):
		return self._timestamp
	def settimestamp(self, value):
		self._timestamp = value
	def deltimestamp(self):
		del self._timestamp
	timestamp = property(gettimestamp, settimestamp, deltimestamp, "timestamp")

	def getchangeset_id(self):
		return self._changeset_id
	def setchangeset_id(self, value):
		self._changeset_id = value
	def delchangeset_id(self):
		del self._changeset_id
	changeset_id = property(getchangeset_id, setchangeset_id, delchangeset_id, "changeset_id")

	def getvisible(self):
		return self._visible
	def setvisible(self, value):
		self._visible = value
	def delvisible(self):
		del self._visible
	visible = property(getvisible, setvisible, delvisible, "visible")
	
class relation(object):
	def __init__(self):
		self._version = None
		self._user_id = None
		self._user = None
		self._id = None
		self._visible = None
		self._tags = {}
		self._members = []
		self._timestamp = None
		self._changeset_id = None

	def getversion(self):
		return self._version
	def setversion(self, value):
		self._version = value
	def delversion(self):
		del self._version
	version = property(getversion, setversion, delversion, "version")

	def getuser_id(self):
		return self._user_id
	def setuser_id(self, value):
		self._user_id = value
	def deluser_id(self):
		del self._user_id
	user_id = property(getuser_id, setuser_id, deluser_id, "user id")

	def getuser(self):
		return self._user
	def setuser(self, value):
		self._user = value
	def deluser(self):
		del self._user
	user = property(getuser, setuser, deluser, "user id")

	def getid(self):
		return self._id
	def setid(self, value):
		self._id = value
	def delid(self):
		del self._id
	id = property(getid, setid, delid, "node id")

	def getvisible(self):
		return self._visible
	def setvisible(self, value):
		self._visible = value
	def delvisible(self):
		del self._visible
	visible = property(getvisible, setvisible, delvisible, "visibility")

	@property
	def tags(self):
		"""I'm the 'tag' property."""
		return self._tags

	@tags.setter
	def x(self, key, value):
		self._tag[key] = value

	@x.deleter
	def x(self):
		del self._x

	def getmembers(self):
		return self._members
	def setmembers(self, value):
		#print "appending " , value , " to members"
		self._members.append(value)
	def delmembers(self, value):
		self._members.remove(value)
	members = property(getmembers, setmembers, delmembers, "members")

	def gettimestamp(self):
		return self._timestamp
	def settimestamp(self, value):
		self._timestamp = value
	def deltimestamp(self):
		del self._timestamp
	timestamp = property(gettimestamp, settimestamp, deltimestamp, "timestamp")

	def getchangeset_id(self):
		return self._changeset_id
	def setchangeset_id(self, value):
		self._changeset_id = value
	def delchangeset_id(self):
		del self._changeset_id
	changeset_id = property(getchangeset_id, setchangeset_id, delchangeset_id, "changeset_id")

	def getvisible(self):
		return self._visible
	def setvisible(self, value):
		self._visible = value
	def delvisible(self):
		del self._visible
	visible = property(getvisible, setvisible, delvisible, "visible")
	
class member(object):
	def __init__(self):
		self._type = None
		self._ref = None
		self._role = None
		self._sequence_id = None

	def gettype(self):
		return self._type
	def settype(self, value):
		self._type = value
	def deltype(self):
		del self._type
	type = property(gettype, settype, deltype, "type")

	def getref(self):
		return self._ref
	def setref(self, value):
		self._ref = value
	def delref(self):
		del self._ref
	ref = property(getref, setref, delref, "ref")

	def getrole(self):
		return self._role
	def setrole(self, value):
		self._role = value
	def delrole(self):
		del self._role
	role = property(getrole, setrole, delrole, "role")

	def getsequence_id(self):
		return self._sequence_id
	def setsequence_id(self, value):
		self._sequence_id = value
	def delsequence_id(self):
		del self._sequence_id
	sequence_id = property(getsequence_id, setsequence_id, delsequence_id, "sequence id")
