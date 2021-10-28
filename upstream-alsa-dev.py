#!/usr/bin/python3

import argparse
import os
import re
import subprocess

def get_maintainer_list(script_path, patch_path):
	maintainer_list = []

	# | sed 's/ *([^)]*) *//g' | sed 's/"//g' | sed 's/^\(.*\)$/--cc="\1" /' | tr -d '\n'

	p1 = subprocess.Popen([script_path, patch_path], stdout = subprocess.PIPE, text = True)
	# remove the supporter info
	p2 = subprocess.Popen(['sed', 's/ *([^)]*) *//g'], stdin = p1.stdout, stdout = subprocess.PIPE, text = True)
	p1.stdout.close()
	# remove the quotation marks
	p3 = subprocess.Popen(['sed', 's/"//g'], stdin = p2.stdout, stdout = subprocess.PIPE, text = True)
	p2.stdout.close()

	outs, errs = p3.communicate()
	#print('outout: %s' % (outs))

	maintainers = str(outs).split('\n')
	print('%d maintainers found' % (len(maintainers)))

	for maintainer in maintainers:
		if len(maintainer) == 0:
			continue

		if maintainer not in maintainer_list:
			#print('  maintainer %s [add to list]' % (maintainer))
			maintainer_list.append(maintainer)
		#else:
		#	print('  maintainer %s' % (maintainer))

	return maintainer_list

def process_patch_file(check_patch_script, get_maintainer_script, patch_file, cc_list):
	print('Patch %s found' % (patch_file))

	output = subprocess.check_output([check_patch_script, patch_file], text = True)
	print('\nCheck patch:\n%s' % (output))

	print('Get maintainer: ', end = '')
	maintainer_list = get_maintainer_list(get_maintainer_script, patch_file)

	# use list instead of set to maintain the order
	for maintainer in maintainer_list:
		if maintainer not in cc_list:
			print('  add %s to cc list' % (maintainer))
			cc_list.append(maintainer)

	return

def main():
	check_patch_script = './scripts/checkpatch.pl'
	get_maintainer_script = './scripts/get_maintainer.pl'
	cc_list = []
	cover_letter = False

	parser = argparse.ArgumentParser()
	parser.add_argument('patch_file', nargs = '?', default = '', help = 'patch file to upstream')

	args = parser.parse_args()

	if os.path.isfile(check_patch_script) == False:
		print('Cannot find the check patch script')
		print('Please run this script under Linux source root directory')
		return

	if os.path.isfile(get_maintainer_script) == False:
		print('Cannot find the get maintainer script')
		print('Please run this script under Linux source root directory')
		return

	prog = re.compile(r'.*\.patch')

	if args.patch_file != '':
		# upstream a specific patch file
		patch_file = os.path.abspath('./' + args.patch_file)

		if os.path.isfile(patch_file) == False:
			print('Patch file does not exist')
			return
		if prog.match(patch_file) == None:
			print('Not a patch file')
			return

		# update the cc list
		process_patch_file(check_patch_script, get_maintainer_script, patch_file, cc_list)
	else:
		# walk in current directory
		for dirpath, dirnames, filenames in os.walk('.'):
			for filename in filenames:
				if filename == '0000-cover-letter.patch':
					# upstream all patch files
					cover_letter = True
					continue

				tmp = os.path.join(dirpath, filename)
				patch_file = os.path.abspath(tmp)

				if prog.match(patch_file) == None:
					continue

				# update the cc list
				process_patch_file(check_patch_script, get_maintainer_script, patch_file, cc_list)

			# no need to walk inside
			break

		if cover_letter == False:
			print('No cover letter found')
			return

	# output the upstream command
	print('\nUpstream command:\ngit send-email --to=alsa-devel@alsa-project.org ', end = '')

	for cc in cc_list:
		print('--cc="%s" ' % (cc), end = '')

	if args.patch_file != '':
		print('--signoff %s' % (args.patch_file))
	else:
		print('--signoff --to-cover --cc-cover ./*.patch')


if __name__ == '__main__':
	main()
