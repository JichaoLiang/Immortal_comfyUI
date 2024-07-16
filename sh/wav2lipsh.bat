R:
cd r:\workspace\wave2lip
CALL C:\ProgramData\Miniconda3\Scripts\activate.bat Q:\condaenv\wave2lip
CALL conda activate wave2lip
Q:\condaenv\wave2lip\python.exe -V
Q:\condaenv\wave2lip\python.exe inference.py --checkpoint ./checkpoints\wav2lip_gan.pth --face %1 --audio %2 --outfile %3