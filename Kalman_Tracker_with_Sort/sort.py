"""
    SORT: A Simple, Online and Realtime Tracker    
"""

import numpy as np
from kalman_tracker import KalmanBoxTracker
from data_association import associate_detections_to_trackers


class Sort(object):
  def __init__(self,max_age = 2 , min_hits = 3):
    """
    Sets key parameters for SORT
    """
    self.max_age = max_age
    self.min_hits = min_hits
    self.trackers = []
    self.frame_count = 0

  def update(self,dets):
    """
    Params:
      dets - a numpy array of detections in the format [[x1,y1,x2,y2,score],[x1,y1,x2,y2,score],...]
    Requires: this method must be called once for each frame even with empty detections.
    Returns the a similar array, where the last column is the object ID.

    NOTE: The number of objects returned may differ from the number of detections provided.
    """
    self.frame_count += 1
    """
    trks   : array of trackers' position with the score of each tracker
    to_del : array that contain indices of trackers need to be deleted as they are invalid 
    ret    : array of returned trackers [pos,id]
    colors : list of colors of the bounding boxes
    """
    trks = np.zeros((len(self.trackers),5)) 
    to_del = []   
    ret = []
    colors=[]
    
    #get predicted locations from existing trackers.
    for t,trk in enumerate(trks):
      pos = self.trackers[t].predict()[0]
      trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
      if(np.any(np.isnan(pos))):
        to_del.append(t)
    trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
    for t in reversed(to_del):
      self.trackers.pop(t)
      
    #Compare detections to trackers and fil the matched, unmatched_dets, unmatched_trks lists  
    matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets,trks)

    #update matched trackers with assigned detections
    for t,trk in enumerate(self.trackers):
      if(t not in unmatched_trks):
        d = matched[np.where(matched[:,1]==t)[0],0]
        trk.update(dets[d,:][0])

    #create and initialise new trackers for unmatched detections
    for i in unmatched_dets:
      trk = KalmanBoxTracker(dets[i,:])
      self.trackers.append(trk)
      
    i = len(self.trackers)
    for trk in reversed(self.trackers):
        if dets == []:
          trk.update([],img) 
        d = trk.get_state()[0]
        i -= 1
        if((trk.time_since_update < 1) and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits )):
          ret.append(np.concatenate((d,[trk.id+1])).reshape(1,-1)) 
          colors.append(trk.color)
        
        #remove dead tracklet
        elif(trk.time_since_update > self.max_age):
          self.trackers.pop(i)
          
        else:
          ret.append(np.concatenate((d,[trk.id+1])).reshape(1,-1))
          colors.append(trk.color)
          
    if(len(ret)>0):
      return np.concatenate(ret),colors
    return np.empty((0,5)),[]
    
