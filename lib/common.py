def get_user_response():
	"""	Accepts yes/no answer as user input and returns answer as boolean
	"""
	while "need response":
		reply = str(input(" Proceed? (y/n) ")).lower().strip()
		if len(reply) > 0:
			if reply[0] == "y":
				response = True
				break
			if reply[0] == "n":
				response = False
				break

	return response

if __name__ == "__main__":
	sys.exit("I am a module, not a script.")