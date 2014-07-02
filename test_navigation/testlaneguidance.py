import ncdb as pymobius
from tesla.spatial.mobius.maneuver import TURN_TYPE_2_COMMAND_MAP

VEHICLE_TYPE_MAP = {
    pymobius.Car : 'car',
    pymobius.Bicycle : 'bicycle',
    pymobius.Truck: 'truck',
}
ROUTE_OPTIMIZATION_MAP = {
    pymobius.RO_Easiest : 'easiest',
    pymobius.RO_Fastest : 'fastest',
    pymobius.RO_Shortest : 'shortest',
}
DIVIDER_MAP = {
    pymobius.LONG_DASHED : 'long-dash-divider',
    pymobius.DOUBLE_SOLID : 'double-solid-divider',
    pymobius.SINGLE_SOLID : 'single-solid-divider',
    pymobius.SOLID_DASHED : 'solid-dash-divider',
    pymobius.DASHED_SOLID : 'dash-solid-divider',
    pymobius.SHORT_DASHED : 'short-dash-divider',
    pymobius.SHADED_AREA : 'shaded-area-divider',
    pymobius.DASHED_BLOCKS : 'block-dash-divider',
    pymobius.PHYS_DIVIDER : 'physical-divider',
    pymobius.DOUBLE_DASHED : 'double-dash-divider',
    pymobius.NONE : 'no-divider',
    pymobius.XING_ALERT : 'crossing-alert-divider',
    pymobius.CTR_TURN_LANE : 'center-turn-line-divider'
}

LANETYPE_MAP = {
    pymobius.LT_REGULAR : 'regular-lane',
    pymobius.LT_HOV : 'hov-lane',
    pymobius.LT_REVERSIBLE : 'reversible-lane',
    pymobius.LT_EXPRESS     : 'express-lane',
    pymobius.LT_ACCEL       : 'acceleration-lane',
    pymobius.LT_DECEL       : 'deceleration-lane',
    pymobius.LT_AUX         : 'auxiliary-lane',
    pymobius.LT_SLOW        : 'slow-lane',
    pymobius.LT_PASSING     : 'passing-lane',
    pymobius.LT_SHOULDER    : 'drivable-shoulder-lane',
    pymobius.LT_REGULATED   : 'regulated-access-lane',
    pymobius.LT_TURN        : 'turn-lane',
    pymobius.LT_CENTER_TURN : 'center-turn-lane',
    pymobius.LT_TRUCK_PARK  : 'truck_parking_lane'
}

ARROW_MAP = {
pymobius.LD_STRAIGHT     : 'straight-arrow',
pymobius.LD_SLIGHT_RIGHT : 'slight-right-arrow',
pymobius.LD_RIGHT        : 'right-arrow',
pymobius.LD_HARD_RIGHT   : 'hard-right-arrow',
pymobius.LD_UTURN_LEFT   : 'u-turn-left-arrow',
pymobius.LD_HARD_LEFT    : 'hard-left-arrow',
pymobius.LD_LEFT         : 'left-arrow',
pymobius.LD_SLIGHT_LEFT  : 'slight-left-arrow',
pymobius.LD_MERGE_RIGHT  : 'merge-right-arrow',
pymobius.LD_MERGE_LEFT   : 'merge-left-arrow',
pymobius.LD_MERGE_LANES  : 'merge-lanes-arrow',
pymobius.LD_UTURN_RIGHT  : 'u-turn-right-arrow',
pymobius.LD_SECOND_RIGHT : 'second-right-arrow',
pymobius.LD_SECOND_LEFT  : 'second-left-arrow'
}
def main():
  mappath = "/nb/nbserver/data/regions/NA_TT/map/main_NA.ini"
  session = pymobius.Session()
  print "Using session_config_file: %s" % mappath
  if session.Open(mappath) != pymobius.NCDB_OK:
    print "Could not open. (%s used)" % mappath
  else:
    print "Open success"
  
  #origin_wp = pymobius.WorldPoint(33.562827, -117.715631)
  #destination_wp = pymobius.WorldPoint(33.589492, -117.735651)
  origin_wp = pymobius.WorldPoint(33.562827, -117.715631)
  destination_wp = pymobius.WorldPoint(33.589492, -117.735651)
  heading = 777.0
  speed = 0.0
  maneuver_options = pymobius.ManeuverOptions()
  maneuver_options.SetWantLaneGuidance(True)
  maneuver_options.SetWantExitNumber(True)
  route = pymobius.Route()
  route.SetDestStreetName(pymobius.UtfString('abcccc dfsd'))
  print 'Destination street name:', route.GetDestStreetName()
  routing_options = pymobius.RoutingOptions()
  routing_options.SetVehicleType(pymobius.Car)
  route_manager = pymobius.RouteManager(session)
  route_manager.SetManeuverOptions(maneuver_options);
  route_manager.InitializeTrafficReader();
  route_manager.ReadHistoricTrafficByProvider("NAVTEQ","/usr/local/nb/nbserver/data/regions/USA/traffic/historical");
  route_manager.UpdateRealTimeDataByProvider("NAVTEQ");
  route_manager.UpdateIncidentDataByProvider("NAVTEQ");
  print "LD_MERGE_LEFT is %r" %pymobius.LONG_DASHED
  #rc = route_manager.CalculateRoute(routing_options,origin_wp,destination_wp,heading,speed,route)
  route_list = []
  routes = [route]
  #rc, route_list= route_manager.CalculateMultiRoutes(routing_options,origin_wp,destination_wp,heading,speed, route)
  rc = route_manager.CalculateRoute(routing_options,origin_wp,destination_wp,heading,speed, route)
  if rc != pymobius.NCDB_OK:
    print "caculate route error"
  else:
    print "caculate route successful"
    route_list = [route]
    for iroute in route_list:
        print "---------------route --------------------------------"
        print "IsBridgeInRoute: %s"% iroute.IsBridgeInRoute()
        print "IsHwyInRoute: %s"% iroute.IsHwyInRoute()
        print "IsTollRoadInRoute = %s" % iroute.IsTollRoadInRoute()
        print 'route destination address:%s' % iroute.GetDestStreetName()
        route_opt = iroute.GetRoutingOptions()
        print "GetRoutingOptions = %s" % route_opt
        opt = route_opt.GetRouteOptimization()
        avoid_segment_list = route_opt.GetAvoidSegmentsWithCost()
        avoid_with_cost_list = []
        for i in avoid_segment_list:
            avoid_with_cost_list.append( (i.m_nodeSegmentId.m_Value, i.m_cost) )
        print "avoid_with_cost_list: %s" %avoid_with_cost_list
        if opt in ROUTE_OPTIMIZATION_MAP:
            print "route optimization %s" %ROUTE_OPTIMIZATION_MAP[opt]
        #print "route vehicle" % route_opt['vehicle']
        #print "route avoids = %s " % route_opt['avoids']
        labelPoint = iroute.GetLabelPoint()
        print "label point %s,%s" % (labelPoint[0], labelPoint[1])
        mobius_maneuvers = iroute.GetManeuverList()
        i = 0
        for mobius_maneuver in mobius_maneuvers:
          print "***********************************************************************"
          i += 1
          lat, lon = mobius_maneuver.getPoint()
          itype =  mobius_maneuver.getTurnType()
          print "maneuver%d point is %s %s" %(i,lat,lon)
          print "mobius_maneuver type: %s, %s" % (itype, TURN_TYPE_2_COMMAND_MAP[itype])
       #routing_optinos = iroute.GetRoutingOptions()
       #print "route option = %s" % routing_optinos
      
  session.Close()
  print "test finished"


if __name__ == '__main__':
    main()
