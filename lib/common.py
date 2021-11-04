def get_yn_answer():
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

def get_choice_from_menu(choices):
	choice = 1
	for option in choices:
		print(" {choice}: {option}".format(choice=choice, option=option))
		choice += 1
	print()

	user_input = 0
	while True:
		try:
			user_input = int(input("Choice: (1-{num_choices}) ".format(num_choices=len(choices))))
			if user_input not in range(1, len(choices)+1):
				continue
			else:
				pass
		except KeyboardInterrupt:
			sys.exit()
		except:
			pass
		else:
			print("\n{choice}".format(choice=choices[user_input-1]))
			break

	return user_input-1

if __name__ == "__main__":
	sys.exit("I am a module, not a script.")