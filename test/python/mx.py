from casadi import *
import casadi as c
from numpy import *
import unittest
from types import *
from helpers import *

def checkarray(self,zr,zt,name):
    if len(zr.shape)==1 and (zt.shape[0]==1 or zt.shape[1]==1) and zr.shape[0]==zt.shape[1]*zt.shape[0]:
      zr=reshape(zr,(zt.shape));
    self.assertEqual(zt.shape[0],zr.shape[0],"%s dimension error. Got %s, expected %s" % (name,str(zt.shape),str(zr.shape)))
    self.assertEqual(len(zt.shape),len(zr.shape),"%s dimension error. Got %s, expected %s" % (name,str(zt.shape),str(zr.shape)))
    self.assertEqual(zt.shape[1],zr.shape[1],"%s dimension error. Got %s, expected %s" % (name,str(zt.shape),str(zr.shape)))
    for i in range(zr.shape[0]):
      for j in range(zr.shape[1]):
        self.assertAlmostEqual(zt[i,j],zr[i,j],10,"%s evaluation error. %s <-> %s" % (name, str(zt),str(zr)))

def checkMXoperations(self,ztf,zrf,name):
    x = MX("x",1,3)
    z=vertcat([x*(i+1) for i in range(8)])
    f = MXFunction([x],[ztf(z)])
    f.init()
    L=[1,2,3]
    f.setInput(L,0)
    f.evaluate()
    zt = f.output(0).toArray()
    zr = array([[L[0]*(i+1),L[1]*(i+1),L[2]*(i+1)] for i in range(8)])
    checkarray(self,zrf(zr),zt,name)
    return (zt,zrf(zr))

def checkMXoperations2(self,ztf,zrf,name):
    x = MX("x",3,1)
    z = horzcat([x*i for i in range(8)])
    f = MXFunction([x],[ztf(z)])
    f.init()
    L=[1,2,3]
    f.setInput(L,0)
    f.evaluate()
    zt = f.output(0).toArray()
    zr = array([[L[0]*i,L[1]*i,L[2]*i] for i in range(8)]).T
    checkarray(self,zrf(zr),zt,name)
    return zt

def checkMXoperations3(self,ztf,zrf,name):
    x = MX("x",3,1)
    p = horzcat([x[0,0],x[1,0],x[2,0]])
    z = vertcat([p*i for i in range(8)])
    f = MXFunction([x],[ztf(z)])
    f.init()
    L=[1,2,3]
    f.setInput(L,0)
    f.evaluate()
    zt = f.output(0).toArray()
    zr = array([[L[0]*i,L[1]*i,L[2]*i] for i in range(8)])
    checkarray(self,zrf(zr),zt,name)
    return (zt,zrf(zr))
    
class MXtests(casadiTestCase):

  def setUp(self):
    pass

  def test_MX1(self):
    self.message("MX constructor")
    x = MX("x",2,3)
    self.assertEqual(x.size1(),2,"MX fails to indicate its size1")
    self.assertEqual(x.size2(),3,"MX fails to indicate its size2")

  def test_MXvertcat(self):
    self.message("MX vertcat")
    x = MX("x",1,3)
    y = MX("y",1,3)
    z=vertcat((x,y))
    self.assertEqual(z.size1(),2,"MX fails to indicate its size1")
    self.assertEqual(z.size2(),3,"MX fails to indicate its size2")

  def test_MXindices(self):
    self.message("MX simple indexing")
    x = MX("x",2,3)
    for i in range(2):
      for j in range(3):
        a = "x(%d,%d)" % (i,j)
        b = str(x[i,j])
        self.assertEqual(a,b,"MX indexing is mixed up")

  # Joel: NOTE this does not work properly
  #def test_MX2(self):
    #U = MX("U",10,2)
    #u = U.getRow(1) # NOTE: the correct syntax should be U[1,:], there is a workaround that allow this, but it is not yet supported in C++

  def test_MXfunction1(self):
    self.message("MXFunction single input, single output")
    # check if x->2*x
    # evaluates correctly for x=3
    x = MX("x")
    y = 2*x
    f = MXFunction([x],[y])
    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),1,"MXFunction fails to indicate correct number of outputs")
    f.init()
    f.setInput(3,0);
    f.evaluate()
    yt = tuple(f.output())
    self.assertEqual(type(yt),TupleType,"Output of MXFunction is expected to be tuple of floats")
    self.assertEqual(len(yt),1,"Output of MXFunction was tuple of floats, as expected, but length is incorrect.")
    y=yt[0]
    self.assertEqual(type(y),float,"Output of MXFunction is expected to be tuple of floats")
    self.assertAlmostEqual(y, 2*3,10)

  def test_MXfunction2(self):
    self.message("MXFunction multi input, multi output")
      # check if [x,y]->[y+x,y*x]
    # evaluates correctly for x=3,y=7
    x = MX("x")
    y = MX("y")
    f = MXFunction([x,y],[x+y,y*x])
    self.assertEqual(f.getNumInputs(),2,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),2,"MXFunction fails to indicate correct number of outputs")

    f.init()
    f.setInput(3,0);
    f.setInput(7,1);
    f.evaluate()
    zt1 = tuple(f.output(0))
    zt2 = tuple(f.output(1))
    self.assertEqual(type(zt1),TupleType,"Output of MXFunction is expected to be tuple of floats")
    self.assertEqual(type(zt2),TupleType,"Output of MXFunction is expected to be tuple of floats")
    self.assertEqual(len(zt1),1,"Output of MXFunction was tuple of floats, as expected, but length is incorrect.")
    self.assertEqual(len(zt2),1,"Output of MXFunction was tuple of floats, as expected, but length is incorrect.")
    z1=zt1[0]
    z2=zt2[0]
    self.assertEqual(type(z1),float,"Output of MXFunction is expected to be tuple of floats")
    self.assertEqual(type(z2),float,"Output of MXFunction is expected to be tuple of floats")
    self.assertAlmostEqual(z2, 21,10)
    self.assertAlmostEqual(z1, 10,10)      



  def test_MXfunction3(self):
    self.message("MXFunction single input, multi output (1)")
    # check if [x,y]->[y+x,y*x]
    # evaluates correctly for x=3,y=7
    # now with single input, multi output
    xy = MX("xy",2)
    f = MXFunction([xy],[xy[0]+xy[1],xy[0]*xy[1]])
    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),2,"MXFunction fails to indicate correct number of outputs")
    f.init()
    f.setInput([3,7],0);
    f.evaluate()
    zt1 = tuple(f.output(0))
    zt2 = tuple(f.output(1))
    self.assertEqual(type(zt1),TupleType,"Output of MXFunction is expected to be tuple of floats")
    self.assertEqual(type(zt2),TupleType,"Output of MXFunction is expected to be tuple of floats")
    self.assertEqual(len(zt1),1,"Output of MXFunction was tuple of floats, as expected, but length is incorrect.")
    self.assertEqual(len(zt2),1,"Output of MXFunction was tuple of floats, as expected, but length is incorrect.")
    z1=zt1[0]
    z2=zt2[0]
    self.assertEqual(type(z1),float,"Output of MXFunction is expected to be tuple of floats")
    self.assertEqual(type(z2),float,"Output of MXFunction is expected to be tuple of floats")
    self.assertAlmostEqual(z2, 21,10)
    self.assertAlmostEqual(z1, 10,10)

  def test_MXfunction3b(self):
    self.message("MXFunction single input, multi output (2)")
    # check if [x,y]->[y+x,y*x]
    # evaluates correctly for x=3,y=7
    # now with single input, multi output
    xy = MX("xy",1,2)
    f = MXFunction([xy],[xy[0]+xy[1],xy[0]*xy[1]])
    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),2,"MXFunction fails to indicate correct number of outputs")
    f.init()
    f.setInput([3,7],0);
    f.evaluate()
    zt1 = f.output(0).toArray()
    zt2 = f.output(1).toArray()
    
    self.assertEqual(type(zt1),ndarray,"Output of MXFunction is expected to be numpy.ndarray")
    self.assertEqual(zt1.shape[0],1,"Output of MXFunction is of wrong shape.")
    self.assertEqual(zt1.shape[1],1,"Output of MXFunction is of wrong shape.")
    
    self.assertEqual(type(zt2),ndarray,"Output of MXFunction is expected to be numpy.ndarray")
    self.assertEqual(zt2.shape[0],1,"Output of MXFunction is of wrong shape.")
    self.assertEqual(zt2.shape[1],1,"Output of MXFunction is of wrong shape.")
    
    z1=zt1[0,0]
    z2=zt2[0,0]
    self.assertEqual(type(z1),float64,"Output of MXFunction is expected to be numpy.ndarray of floats")
    self.assertEqual(type(z2),float64,"Output of MXFunction is expected to be numpy.ndarray of floats")
    self.assertAlmostEqual(z2, 21,10)
    self.assertAlmostEqual(z1, 10,10)

  def test_MXfunction4(self):
    self.message("MXFunction single input, single output , using vertcat")
    # check if [x,y]->[y+x,y*x]
    # evaluates correctly for x=3,y=7
    # now with single input, single output
    xy = MX("xy",2)
    z=vertcat([xy[0]+xy[1],xy[0]*xy[1]])
    f = MXFunction([xy],[z])
    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),1,"MXFunction fails to indicate correct number of outputs")
    f.init()
    f.setInput([3,7],0);
    f.evaluate()
    zt=f.output(0).toArray()
    self.assertEqual(type(zt),ndarray,"Output of MXFunction is expected to be numpy.ndarray")
    self.assertEqual(zt.shape[0],2,"Output of MXFunction is of wrong shape.")
    self.assertEqual(zt.shape[1],1,"Output of MXFunction is of wrong shape.")
    z1=zt[0,0]
    z2=zt[1,0]
    self.assertEqual(type(z1),float64,"Output of MXFunction is expected to be numpy.ndarray of floats")
    self.assertEqual(type(z2),float64,"Output of MXFunction is expected to be numpy.ndarray of floats")
    self.assertAlmostEqual(z2, 21,10)
    self.assertAlmostEqual(z1, 10,10)

  def test_MXfunction5(self):
    self.message("MXFunction single input, single output , using horzcat")
    # check if [x,y]->[y+x,y*x]
    # evaluates correctly for x=3,y=7
    # now with single input, single output
    xy = MX("xy",2)
    z=horzcat([xy[0]+xy[1],xy[0]*xy[1]])
    f = MXFunction([xy],[z])
    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),1,"MXFunction fails to indicate correct number of outputs")
    f.init()
    f.setInput([3,7],0);
    f.evaluate()
    zt = f.output(0).toArray()
    self.assertEqual(type(zt),ndarray,"Output of MXFunction is expected to be numpy.ndarray")
    self.assertEqual(zt.shape[0],1,"Output of MXFunction is of wrong shape.")
    self.assertEqual(zt.shape[1],2,"Output of MXFunction is of wrong shape.")
    z1=zt[0,0]
    z2=zt[0,1]
    self.assertEqual(type(z1),float64,"Output of MXFunction is expected to be numpy.ndarray of floats")
    self.assertEqual(type(z2),float64,"Output of MXFunction is expected to be numpy.ndarray of floats")
    self.assertAlmostEqual(z2, 21,10)
    self.assertAlmostEqual(z1, 10,10)

  #def test_MXslice(self):
    #x = MX("x",1,3)
    #z=x[:]
    #self.assertEqual(z.size1(),1,"Flatten returns MX of wrong dimension")
    #self.assertEqual(z.size2(),3,"Flatten returns MX of wrong dimension")
    #f = MXFunction([x],[z])
    #f.init()
    #L=[1,2,3]
    #f.setInput(L,0)
    #f.evaluate()
    #zt = f.output(0).toArray()
    
    #for i in range(3):
      #self.assertAlmostEqual(L[i], zt[i],10)
      
  #def test_MXslice(self):
    #x = MX("x",3,1)
    #z=x[:]
    #self.assertEqual(z.size1(),3,"Flatten returns MX of wrong dimension")
    #self.assertEqual(z.size2(),1,"Flatten returns MX of wrong dimension")
    #f = MXFunction([x],[z])
    #f.init()
    #L=[1,2,3]
    #f.setInput(L,0)
    #f.evaluate()
    #zt = f.output(0).toArray()
    
    #for i in range(3):
      #self.assertAlmostEqual(L[i], zt[i],10)
        
  def test_identitySX(self):
    self.message("identity SXFunction")
    x = SX("x")
    f = SXFunction([[x]],[[x]])
    f.init()
    f.setInput([3],0)
    f.evaluate()
    self.assertAlmostEqual(f.output(0)[0,0], 3,10)

  def test_identityMX(self):
    self.message("identity MXFunction")
    x = MX("x")
    f  = MXFunction([x],[x])
    f.init()
    f.setInput([3],0)
    f.evaluate()
    self.assertAlmostEqual(f.output(0)[0,0], 3,10)
    
  def test_MXorder(self):
    self.message("MXFunction order of non-zero elements")
    x = MX("x",2,3)
    f = MXFunction([x],[x+x])

    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),1,"MXFunction fails to indicate correct number of outputs")
    f.init()
    L=[1,2,3,4,5,6]
    f.setInput(L,0)
    f.evaluate()
    zt = f.output(0).toArray()
    self.assertEqual(zt.shape[0],2,"Output of MXFunction is of wrong shape.")
    self.assertEqual(zt.shape[1],3,"Output of MXFunction is of wrong shape.")
      
    Lr=reshape(L,(2,3))
    for i in range(2):
      for j in range(3):
        self.assertAlmostEqual(Lr[i,j]*2, zt[i,j],10)
    
  def test_MXtrans(self):
    self.message("trans(MX)")
    x = MX("x",2,3)
    z=trans(x)
    self.assertEqual(z.size1(),3,"Flatten returns MX of wrong dimension")
    self.assertEqual(z.size2(),2,"Flatten returns MX of wrong dimension")
    f = MXFunction([x],[z])
    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),1,"MXFunction fails to indicate correct number of outputs")
    f.init()
    L=[1,2,3,4,5,6]
    f.setInput(L,0)
    f.evaluate()
    zt = f.output(0).toArray()
    
    ztr=reshape(zt,(3,2))
    Lr=reshape(L,(2,3))
    for i in range(2):
      for j in range(3):
        self.assertAlmostEqual(Lr[i,j], ztr[j,i],10)
    
  def test_MXflatten(self):
    self.message("trans(MX)")
    x = MX("x",2,3)
    z=flatten(x)
    self.assertEqual(z.size1(),6,"Flatten returns MX of wrong dimension")
    self.assertEqual(z.size2(),1,"Flatten returns MX of wrong dimension")
    f = MXFunction([x],[z])
    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),1,"MXFunction fails to indicate correct number of outputs")
    f.init()
    L=[1,2,3,4,5,6]
    f.setInput(L,0)
    f.evaluate()
    zt = f.output(0).toArray()
    for i in range(len(L)):
      self.assertAlmostEqual(L[i], zt[i],10)
      
    
  def test_MXreshape(self):
    self.message("reshape(MX)")
    x = MX("x",2,3)
    z=c.reshape(x,(1,6))
    self.assertEqual(z.size1(),1,"Flatten returns MX of wrong dimension")
    self.assertEqual(z.size2(),6,"Flatten returns MX of wrong dimension")
    f = MXFunction([x],[z])
    self.assertEqual(f.getNumInputs(),1,"MXFunction fails to indicate correct number of inputs")
    self.assertEqual(f.getNumOutputs(),1,"MXFunction fails to indicate correct number of outputs")
    f.init()
    L=[1,2,3,4,5,6]
    f.setInput(L,0)
    f.evaluate()
    zt = f.output(0).toArray()
    for i in range(len(L)):
      self.assertAlmostEqual(L[i], zt[0,i],10)
  
  def test_MXcompose(self):
    self.message("compositions of flatten, trans, reshape with vertcat")
    checkMXoperations(self,lambda x: x,lambda x: x,'vertcat')
    checkMXoperations(self,lambda x: trans(x),lambda x: x.T,'trans(vertcat)')
    checkMXoperations(self,lambda x: trans(trans(x)),lambda x: x,'trans(trans(vertcat))')
    checkMXoperations(self,lambda x: flatten(trans(x)),lambda x: reshape(x.T,(prod(x.shape),1)),'flatten(trans(vertcat))')
    checkMXoperations(self,lambda x: trans(flatten(x)),lambda x: reshape(x,(prod(x.shape),1)).T,'flatten(trans(vertcat))')
    checkMXoperations(self,lambda x: c.reshape(x,(4,6)),lambda x: reshape(x,(4,6)),'reshape(vertcat)')
    checkMXoperations(self,lambda x: c.reshape(trans(x),(4,6)),lambda x: reshape(x.T,(4,6)),'reshape(trans(vertcat))') 
    checkMXoperations(self,lambda x: trans(c.reshape(x,(4,6))),lambda x: reshape(x,(4,6)).T,'trans(reshape(vertcat))') 

  def test_MXcompose2(self):
    self.message("compositions of flatten, trans, reshape with horzcat")
    checkMXoperations2(self,lambda x: x,lambda x: x,'horzcat')
    checkMXoperations2(self,lambda x: trans(x),lambda x: x.T,'trans(horzcat)')
    checkMXoperations2(self,lambda x: trans(trans(x)),lambda x: x,'trans(trans(horzcat))')
    checkMXoperations2(self,lambda x: flatten(trans(x)),lambda x: reshape(x.T,(prod(x.shape),1)),'flatten(trans(horzcat))')
    checkMXoperations2(self,lambda x: trans(flatten(x)),lambda x: reshape(x,(prod(x.shape),1)).T,'flatten(trans(horzcat))')
    checkMXoperations2(self,lambda x: c.reshape(x,(4,6)),lambda x: reshape(x,(4,6)),'reshape(horzcat)')
    checkMXoperations2(self,lambda x: c.reshape(trans(x),(4,6)),lambda x: reshape(x.T,(4,6)),'reshape(trans(horzcat))') 
    checkMXoperations2(self,lambda x: trans(c.reshape(x,(4,6))),lambda x: reshape(x,(4,6)).T,'trans(reshape(horzcat))') 

  def test_MXcompose3(self):
    self.message("compositions of flatten, trans, reshape with vertcat")
    checkMXoperations3(self,lambda x: x,lambda x: x,'snippet')
    checkMXoperations3(self,lambda x: trans(x),lambda x: x.T,'trans(snippet)')
    checkMXoperations3(self,lambda x: trans(trans(x)),lambda x: x,'trans(trans(snippet))')
    checkMXoperations3(self,lambda x: flatten(trans(x)),lambda x: reshape(x.T,(prod(x.shape),1)),'flatten(trans(snippet))')
    checkMXoperations3(self,lambda x: trans(flatten(x)),lambda x: reshape(x,(prod(x.shape),1)).T,'flatten(trans(snippet))')
    checkMXoperations3(self,lambda x: c.reshape(x,(4,6)),lambda x: reshape(x,(4,6)),'reshape(snippet)')
    checkMXoperations3(self,lambda x: c.reshape(trans(x),(4,6)),lambda x: reshape(x.T,(4,6)),'reshape(trans(snippet))') 
    checkMXoperations3(self,lambda x: trans(c.reshape(x,(4,6))),lambda x: reshape(x,(4,6)).T,'trans(reshape(snippet))') 

  def test_MXcompose4(self):
    self.message("compositions of horzcat + vertcat")
    checkMXoperations(self,lambda x: vertcat([x]),lambda x: x,'vertcat(vertcat)')
    checkMXoperations(self,lambda x: vertcat([x,x*2]),lambda x: vstack((x,x*2)),'vertcat(vertcat,vertcat)')
    checkMXoperations(self,lambda x: horzcat([x]),lambda x: x,'horzcat(vertcat)')
    checkMXoperations(self,lambda x: horzcat([x,x*2]),lambda x: hstack((x,x*2)),'horzcat(vertcat,vertcat)')
    
    checkMXoperations2(self,lambda x: vertcat([x]),lambda x: x,'vertcat(horzcat)')
    checkMXoperations2(self,lambda x: vertcat([x,x*2]),lambda x: vstack((x,x*2)),'vertcat(horzcat,horzcat)')
    checkMXoperations2(self,lambda x: horzcat([x]),lambda x: x,'horzcat(horzcat)')
    checkMXoperations2(self,lambda x: horzcat([x,x*2]),lambda x: hstack((x,x*2)),'horzcat(horzcat,horzcat)')
    
    checkMXoperations3(self,lambda x: vertcat([x]),lambda x: x,'vertcat(snippet)')
    checkMXoperations3(self,lambda x: vertcat([x,x*2]),lambda x: vstack((x,x*2)),'vertcat(snippet,snippet)')
    checkMXoperations3(self,lambda x: horzcat([x]),lambda x: x,'horzcat(snippet)')
    checkMXoperations3(self,lambda x: horzcat([x,x*2]),lambda x: hstack((x,x*2)),'horzcat(snippet,snippet)')
    
  def test_MXslicingnew(self):
    self.message("MX slicing")

    x = MX("x",3,2)
    x0=array([[0.738,0.2],[ 0.1,0.39 ],[0.99,0.999999]])
    self.numpyEvaluationCheck(lambda x:x[0][1,0],lambda x: x[1,0],[x],x0,'x[1,0]')
    self.numpyEvaluationCheck(lambda x:x[0][0,1],lambda x: x[0,1],[x],x0,'x[0,1]')
    self.numpyEvaluationCheck(lambda x: x[0][:,0], lambda x: matrix(x)[:,0],[x],x0,name="x[:,0]")
    self.numpyEvaluationCheck(lambda x: x[0][:,1], lambda x: matrix(x)[:,1],[x],x0,name="x[:,1]")
    self.numpyEvaluationCheck(lambda x: x[0][1,:], lambda x: matrix(x)[1,:],[x],x0,name="x[1,:]")
    self.numpyEvaluationCheck(lambda x: x[0][0,:], lambda x: matrix(x)[0,:],[x],x0,name="x[0,:]")
    self.numpyEvaluationCheck(lambda x: x[0][-1,:], lambda x: matrix(x)[-1,:],[x],x0,name="x[-1,:]")
    self.numpyEvaluationCheck(lambda x: x[0][:,-2], lambda x: matrix(x)[:,-2],[x],x0,name="x[:,-2]")
    self.numpyEvaluationCheck(lambda x: x[0][0:-2,0:-1], lambda x: matrix(x)[0:-2,0:-1],[x],x0,name="x[0:-2,0:-1]")
    self.numpyEvaluationCheck(lambda x: x[0][0:2,0:2], lambda x: matrix(x)[0:2,0:2],[x],x0,name="x[0:2,0:2]")
    #self.numpyEvaluationCheck(lambda x: x[[0,1],0:1],lambda x: x[[0,1],0:1],[x],x0,name='x[:,0:1]')
    #self.numpyEvaluationCheck(lambda x: x[0:1,[0,1]],lambda x: x[0:1,[0,1]],[x],x0,name='x[0:1,:]')
    
  def test_getinputMX(self):
    self.message("outputMX/inputMX")
    x=MX("x",2,3)
    f = MXFunction([x],[3*x]) 
    g = MXFunction([f.inputMX()],[6*f.outputMX()]) 
    
    f.init()
    g.init()
    n=[1,2,3,4,5,6]
    f.setInput(n)
    f.evaluate()
    g.setInput(n)
    g.evaluate()
    checkarray(self,6*f.output().toArray(),g.output().toArray(),"slicing(trans)")
    
    
if __name__ == '__main__':
    unittest.main()

