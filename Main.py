import os
import glob
import pylinac
import numpy as np
import matplotlib
# matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

OUT_DIR = 'Log File Analysis'

class LogFileAnalyzer: 
	def __init__(self):
		## Enter File Name and create folder for storing the results
		fname = input('Enter File or Folder name containing log file: \n')
		if os.path.isdir(fname): 
			BATCH_MODE = True
			print('----------------------------------------')
			print('Batch Mode')
			print('----------------------------------------')
		elif os.path.isfile(fname): 
			BATCH_MODE = False
			print('----------------------------------------')
			print('File Mode')
			print('----------------------------------------')
		else: 
			raise Exception('No such file or folder in the directory...')

		if not os.path.isdir(OUT_DIR): 
			os.mkdir(OUT_DIR)

		## Perform the Main Analysis
		if BATCH_MODE:
			files = glob.glob(fname + '/*')
			for filename in files: 
				# try: 
				self._AnalyzeEachFile(filename)
				print('Finished Analyzing %s ...' %os.path.split(filename)[1])
				# except:
				# 	print('Analysis fail for %s ...' %os.path.split(filename)[1])
		else: 
			try: 
				self._AnalyzeEachFile(fname)
				print('Finished Analyzing %s ...' %fname)
			except:
				print('Analysis fail for %s ...' %fname)

	def _AnalyzeEachFile(self, fname): 
		tlog = pylinac.TrajectoryLog(fname)

		## Access all elements in the tlog
		header   	  = tlog.header.header
		version  	  = tlog.header.version
		subbeams 	  = tlog.header.num_subbeams
		sampling_time = tlog.header.sampling_interval / 1000 ## in seconds 

		# num_snapshots = tlog.axis_data.num_snapshots
		controlpoint  = tlog.axis_data.control_point
		coll   	      = tlog.axis_data.collimator
		gantry        = tlog.axis_data.gantry
		jaws          = tlog.axis_data.jaws
		beamhold      = tlog.axis_data.beam_hold
		mu			  = tlog.axis_data.mu
		mlc 		  = tlog.axis_data.mlc

		numMovingLeaves = mlc.num_moving_leaves
		num_beamholds = tlog.num_beamholds 

		# print(header, version, subbeams, sampling_time)

		### Analyze Results and save as a page in pdf
		with PdfPages(os.path.join(OUT_DIR, os.path.split(fname)[1][0:-4] + '.pdf')) as pdf: 
			## Cover page
			coverpage = plt.figure(figsize=(12, 9))
			coverpage.clf()
			txt1 = 'File Name: ' + fname + '\n' 
			txt2 = 'Header: ' + header + '\nVersion: ' + str(version) + '\n'
			txt3 = 'Number of subbeams: ' + str(subbeams) + '\n'
			txt4 = 'Number of Moving Leaves: ' + str(numMovingLeaves) + '\n'
			txt5 = 'Number of Beam hold: ' + str(num_beamholds) + '\n'
			coverpage.text(0.5, 0.5, txt1+txt2+txt3+txt4+txt5, size = 16, ha="center", transform=coverpage.transFigure)
			pdf.savefig()
			plt.close()
			self._PlotMU(controlpoint, mu, pdf, sampling_time)
			self._PlotMLC(controlpoint, mlc, pdf, sampling_time)
			self._PlotGantry(controlpoint, gantry, pdf)
			self._PlotCollimator(controlpoint, coll, pdf)

	def _PlotMU(self, controlpoint, mu, pdf_ptr, sampling_time):
		plt.figure(figsize=(12, 9))
		plt.subplot(3,1,1)
		plt.plot(controlpoint.actual, mu.actual, 'b-', lineWidth=3, label='Actual')
		plt.plot(controlpoint.actual, mu.expected, 'r-', lineWidth=3, label='Expected')
		plt.ylabel('MU', fontsize=18)
		plt.legend()
		plt.subplot(3,1,2)
		plt.plot(controlpoint.actual, mu.difference, 'k-', lineWidth=3, label='Difference')
		plt.plot([min(controlpoint.actual), max(controlpoint.actual)], [0, 0], 'r:', lineWidth=2)
		plt.ylabel('MU', fontsize=18)
		plt.legend()
		plt.subplot(3,1,3)
		plt.plot(controlpoint.actual[1::], np.diff(mu.actual) / sampling_time * 60, 'b-', lineWidth=3, label='Actual')
		plt.plot(controlpoint.actual[1::], np.diff(mu.expected) / sampling_time * 60, 'r-', lineWidth=3, label='Expected')
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('Dose Rate (MU/min)', fontsize=18)
		plt.legend()
		# plt.subplot(4,1,4)
		# plt.plot(controlpoint.actual, beamhold.actual, 'b-', lineWidth=3, label='Actual')
		# plt.xlabel('Actual Control Point', fontsize=18)
		# plt.ylabel('Beam Hold', fontsize=18)
		# plt.legend()
		pdf_ptr.savefig()
		plt.close()

	def _PlotMLC(self, controlpoint, mlc, pdf_ptr, sampling_time):
		error_bankA = []
		error_bankB = []
		speed_bankA = []
		speed_bankB = []
		speed_error_bankA = []
		speed_error_bankB = []
		leaveNumber = []
		for k in range(mlc.num_leaves):
			if mlc.leaf_moved(k+1): 
				leaveNumber.append(k+1)
				if k < 60:
					error_bankA.append(mlc.leaf_axes[k+1].difference)
					speed_bankA.append(np.diff(mlc.leaf_axes[k+1].actual) / sampling_time)
					speed_error_bankA.append(np.diff(mlc.leaf_axes[k+1].actual) / sampling_time - np.diff(mlc.leaf_axes[k+1].expected) / sampling_time)
				else:
					error_bankB.append(mlc.leaf_axes[k+1].difference)
					speed_bankB.append(np.diff(mlc.leaf_axes[k+1].actual) / sampling_time)
					speed_error_bankB.append(np.diff(mlc.leaf_axes[k+1].actual) / sampling_time - np.diff(mlc.leaf_axes[k+1].expected) / sampling_time)
		# print(leaveNumber)
		plt.figure(figsize=(12, 9))
		plt.subplot(3,1,1)
		plt.hist(np.array(error_bankA).flatten(), density = True, bins = 50, label='Bank A Error')
		plt.hist(np.array(error_bankB).flatten(), density = True, bins = 50, label='Bank B Error', alpha=0.5, color='r')
		plt.ylabel('Probability')
		plt.xlabel('MLC Leaves Error (cm)');
		plt.legend()
		plt.yscale('log')
		plt.subplot(3,1,2)
		plt.hist(np.array(speed_bankA).flatten(), density = True, bins = 50, label='Bank A Speed')
		plt.hist(np.array(speed_bankB).flatten(), density = True, bins = 50, label='Bank B Speed', alpha=0.5, color='r')
		plt.ylabel('Probability')
		plt.xlabel('MLC Leaves Speed (cm/s)');
		plt.legend()
		plt.yscale('log')
		plt.subplot(3,1,3)
		plt.hist(np.array(speed_error_bankA).flatten(), density = True, bins = 50, label='Bank A Speed Error')
		plt.hist(np.array(speed_error_bankB).flatten(), density = True, bins = 50, label='Bank B Speed Error', alpha=0.5, color='r')
		plt.ylabel('Probability')
		plt.xlabel('MLC Leaves Speed Error(cm/s)');
		plt.legend()
		plt.yscale('log')
		pdf_ptr.savefig()
		plt.close()

		plt.figure(figsize=(12, 9))
		plt.subplot(2,1,1)
		for k in range(int(len(leaveNumber)/2)):
			plt.plot(controlpoint.actual[1::], np.diff(mlc.leaf_axes[leaveNumber[k]].actual) / sampling_time, lineWidth=2, label=str(leaveNumber[k]))
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('Leave Speed (mm/s)', fontsize=18)
		plt.legend()
		plt.subplot(2,1,2)
		for k in range(int(len(leaveNumber)/2)+1, len(leaveNumber)):
			plt.plot(controlpoint.actual[1::], np.diff(mlc.leaf_axes[leaveNumber[k]].actual) / sampling_time, lineWidth=2, label=str(leaveNumber[k]))
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('Leave Speed (mm/s)', fontsize=18)
		plt.legend()
		pdf_ptr.savefig()
		plt.close()
		
		plt.figure(figsize=(12, 9))
		plt.subplot(2,1,1)
		for k in range(int(len(leaveNumber)/2)):
			plt.plot(controlpoint.actual, mlc.leaf_axes[leaveNumber[k]].difference, lineWidth=2, label=str(leaveNumber[k]))
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('MLC Leave Error (mm)', fontsize=18)
		plt.legend()
		plt.subplot(2,1,2)
		for k in range(int(len(leaveNumber)/2)+1, len(leaveNumber)):
			plt.plot(controlpoint.actual, mlc.leaf_axes[leaveNumber[k]].difference, lineWidth=2, label=str(leaveNumber[k]))
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('MLC Leave Error (mm)', fontsize=18)
		plt.legend()
		pdf_ptr.savefig()
		plt.close()


	def _PlotGantry(self, controlpoint, gantry, pdf_ptr):
		plt.figure(figsize=(12, 9))
		plt.subplot(2,1,1)
		plt.plot(controlpoint.actual, gantry.actual, 'b-', lineWidth=3, label='Actual')
		plt.plot(controlpoint.actual, gantry.expected, 'r-', lineWidth=3, label='Expected')
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('Gantry Angle', fontsize=18)
		plt.legend()
		plt.subplot(2,1,2)
		plt.plot(controlpoint.actual, gantry.difference, 'k-', lineWidth=3, label='Difference')
		plt.plot([min(controlpoint.actual), max(controlpoint.actual)], [0, 0], 'r:', lineWidth=2)
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('Gantry Angle Error', fontsize=18)
		plt.legend()
		pdf_ptr.savefig()
		plt.close()

	def _PlotCollimator(self, controlpoint, coll, pdf_ptr):
		plt.figure(figsize=(12, 9))
		plt.subplot(2,1,1)
		plt.plot(controlpoint.actual, coll.actual, 'b-', lineWidth=3, label='Actual')
		plt.plot(controlpoint.actual, coll.expected, 'r-', lineWidth=3, label='Expected')
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('Collimator Angle', fontsize=18)
		plt.legend()
		plt.subplot(2,1,2)
		plt.plot(controlpoint.actual, coll.difference, 'k-', lineWidth=3, label='Difference')
		plt.plot([min(controlpoint.actual), max(controlpoint.actual)], [0, 0], 'r:', lineWidth=2)
		plt.xlabel('Actual Control Point', fontsize=18)
		plt.ylabel('Collimator Angle Error', fontsize=18)
		plt.legend()
		pdf_ptr.savefig()
		plt.close()

if __name__ == '__main__':
	LogFileAnalyzer()