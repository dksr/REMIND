import os
import re

def replace_string_in_file(infilePath, outfilePath, findreplace):
   
   print 'reading:', infilePath
   input = open(infilePath,'rb')
   s=input.read()
   input.close()

   numRep=None
   for couple in findreplace:
      if numRep == None:
         numRep = re.search(couple[0],s)
      outtext = re.sub(couple[0],couple[1], s)
      s=outtext

   if numRep:
      print ' writing:', outfilePath
      outF = open(outfilePath,'w')
      outF.write(outtext)
      outF.truncate()
      outF.close()

if __name__ == "__main__":
   in_dir= '/tmp/xml_dir/'
   out_dir= '/tmp/xml_out_dir/'
      
   find_replace = [   
      (re.compile(ur'''<PatientsName>.*</PatientsName>''',re.U|re.M),
      ur'''patient_name'''), 
      (re.compile(ur'''<DoctorsName>.*</DoctorsName>''',re.U|re.M),
      ur'''doctor_name'''), 
      
      # more regex pairs here
      ]
   
   for ifile in os.listdir(in_dir):  
      replace_string_in_file(os.path.join(in_dir, ifile), os.path.join(out_dir, ifile), find_replace)
   
   print 'done'
