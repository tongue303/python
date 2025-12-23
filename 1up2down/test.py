import PulsationThreshold_1up2down as ps
import matplotlib.pyplot as plt
import numpy as np

#sig = np.ones(100)
#sig2 = ps.cosine_ramp(sig,20)
#plt.plot(sig2)

#sig1 = ps.build_signal1(ps.ExperimentParams,-200)
#sig2 = ps.build_signal2(ps.ExperimentParams,-200)
#time = np.arange(len(sig1))/44100
#plt.plot(time*1000,sig1)
#plt.plot(time*1000,sig2)
#plt.show()

noise_amp = ps.db_to_amp(ps.ExperimentParams.noise_level_dbfs)
sig = ps.lowpass_noise(1,44100,1100,noise_amp,0.02)
plt.psd(sig,NFFT=4096,Fs=44100)
plt.xscale('log')
plt.grid(True)
#plt.ylim([-100,-50])
plt.show()

Ltot = ps.ExperimentParams.noise_level_dbfs
Ld = Ltot - 10*np.log10(1000)
print(Ld)