##
# Quick & Dirty 8bit tone generator.
#
##

import math

def generateTone(sampleRate, tone):
	"""
	Generates a tone at tone Hz, sampled at sampleRate Hz,
	in 8 bits.
	Returns a list of 8 bit values as characters.
	"""
	ret = []

	# We sample a sin period each sampleRate/tone.
	steps = float(sampleRate) / float(tone)

	for i in range(int(steps)):
		val = math.sin(2*math.pi*float(i) / steps)
		# Normalize the value between 0..1
		val = (val + 1.0) / 2.0
		# Now maps it to a 8 bit integer
		ret.append(chr(int(val * 255.0)))
	
	return ret


if __name__ == '__main__':
	import sys
	sampleRate = 8000
	tone = 400

	if len(sys.argv) > 1:
		tone = int(sys.argv[1])
	

	print "8 bit, sample rate %s, tone %s: " % (sampleRate, tone)
	print repr(''.join(generateTone(sampleRate, tone)))
