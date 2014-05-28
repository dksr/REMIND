import	cherrypy
import	socket
import	math

import cPickle as pickle
import	openFlashChart
from	openFlashChart_varieties import Bar_Stack, bar_stack_value, x_axis_label, x_axis_labels


class OFC:

    @cherrypy.expose
    def index(self):
        graphs = []
        #self.ifile = ifile 
        # Bar Charts
        graphs.append(openFlashChart.flashHTML('100%', '800', '/my_bar_stack', '/flashes/'))
        graphs.append(openFlashChart.flashHTML('100%', '800', '/ilp_filtered_bar_stack_0', '/flashes/'))
        graphs.append(openFlashChart.flashHTML('100%', '800', '/ilp_filtered_bar_stack_1', '/flashes/'))
        graphs.append(openFlashChart.flashHTML('100%', '800', '/ilp_filtered_bar_stack_2', '/flashes/'))
        graphs.append(openFlashChart.flashHTML('100%', '800', '/ilp_filtered_bar_stack_3', '/flashes/'))
       
        #graphs.append(openFlashChart.flashHTML('100%', '800', '/ilp_filtered_bar_stack_vrac', '/flashes/'))
   
        graphs.append(self.source("html_snippet.html"))

        return self.source("OFC.htm") %({"chart": "<br/><br/><br/><br/>".join(graphs)})

    @cherrypy.expose
    def my_bar_stack(self):
        event_codes = {'GPU_Arrival':              '#FF6600',
                       'Handler_Deposites_Chocks': '#50284A',
                       'Aircraft_Arrival':         '#339900',
                       'Jet_Bridge_Positioning':   '#6699CC',
                       #'Container_Front_Unloading':'#660000',
                       #'Container_Front_Loading':  '#CC3333',
                       'Push_Back_Positioning':    '#FFF000',
                       #'Container_Back_Loading':   '#FF3333',
                       'Jet_Bridge_Parking':       '#0066CC',
                       'Aircraft_Departure':       '#99FF33',
                       'VRAC_Back_Unloading':      '#FF99FF',
                       #'Refuelling':               '#FF6600',
                       'VRAC_Back_Loading':        '#9933FF',
                       'No_Event':                 '#FFFFFF' 
                       }
        gt_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/global_model/' + 'ground_truth_all.p';     
        gt = pickle.load(open(gt_file))
        gt_event_lists = gt['event_lists']
    
        plot = Bar_Stack(colours = ['#C4D318', '#50284A', '#7D7B6A','#ff0000','#ff00ff'])
        
        for eve in event_codes:
            plot.append_keys(event_codes[eve], eve, 13)

        videos = gt_event_lists
        for e in videos:
            # val for each strip in a stack is just the length of the strip.
            # So just keep on laying strips in the stack with length equal to length of interval
            # First start with empty event
            stack   = []            
            val     = e[0][0]
            colour  = event_codes['No_Event']
            tooltip = '(%d, %d)' %(0, e[0][0])
            stack.append(bar_stack_value(val, colour, tooltip))
            

            for i in range(len(e)):
                val = e[i][1] - e[i][0]
                colour = event_codes.get(e[i][2],'#FFFFFF')
                tooltip = '%s <br> Intv: (%d, %d)' %(e[i][2], e[i][0], e[i][1])
                stack.append(bar_stack_value(val, colour, tooltip))
                
                if i != len(e) - 1:
                    # Add empty event after every event
                    val = e[i+1][0] - e[i][1]
                    colour  = event_codes['No_Event']
                    tooltip = '(%d, %d)' %(e[i][1], e[i+1][0])
                    stack.append(bar_stack_value(val, colour, tooltip))
                   
            plot.append_stack(stack)
            
        chart = openFlashChart.template("Ground Truth", style = '{font-size: 20px; color: #F24062; text-align: center;}')
        chart.set_tooltip(behaviour = 'hover')
        chart.set_bg_colour('#FFFFFF')

        # Prepare x_lables
        xlabels = []
        for i in xrange(len(videos)):
            xlabels.append('vid_' + repr(i))            
            
        chart.set_x_axis(labels = x_axis_labels(labels = xlabels))
        chart.set_y_axis(min = 0, max = 35000, steps = 500)
        chart.add_element(plot)

        return chart.encode()
    
    @cherrypy.expose
    def ilp_filtered_bar_stack_0(self):
        event_codes = {'GPU_Arrival':              '#FF6600',
                       'Handler_Deposites_Chocks': '#50284A',
                       'Aircraft_Arrival':         '#339900',
                       'Jet_Bridge_Positioning':   '#6699CC',
                       #'Container_Front_Unloading':'#660000',
                       #'Container_Front_Loading':  '#CC3333',
                       'Push_Back_Positioning':    '#FFF000',
                       #'Container_Back_Loading':   '#FF3333',
                       'Jet_Bridge_Parking':       '#0066CC',
                       'Aircraft_Departure':       '#99FF33',
                       'VRAC_Back_Unloading':      '#FF99FF',
                       #'Refuelling':               '#FF6600',
                       'VRAC_Back_Loading':        '#9933FF',
                       'No_Event':                 '#FFFFFF' 
                       }

        plot = Bar_Stack(colours = ['#C4D318', '#50284A', '#7D7B6A','#ff0000','#ff00ff'])
    
        for eve in event_codes:
            plot.append_keys(event_codes[eve], eve, 13)

        vid = 0    
        # Get ground truth
        gt_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/global_model_ILP/' + 'ground_truth.p';     
        gt = pickle.load(open(gt_file))
        gt_event_lists = gt['event_lists']
        # Only add first video ground truth
        videos = [gt_event_lists[vid]]
        
        # Now the retrieved events
        ilp_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/new_gt_with_zone_1protos_oct/' + 'retrieved_ins_ILP_vis_filtered_events_0.p';
        re = pickle.load(open(ilp_file))
        re_event_ins_lists = re['event_lists']
        ind = 0
        for e in re_event_ins_lists:
            videos.append(e)
            ind += 1
            if ind > 7:
                break
                      
        ind = 0
        for e in videos:
            e.sort()
            # val for each strip in a stack is just the length of the strip.
            # So just keep on laying strips in the stack with length equal to length of interval
            # First start with empty event
            stack   = []            
            val     = e[0][0]
            colour  = event_codes['No_Event']
            tooltip = '(%d, %d)' %(0, e[0][0])
            stack.append(bar_stack_value(val, colour, tooltip))
        
            for i in range(len(e)):                
                val = e[i][1] - e[i][0]
                colour = event_codes.get(e[i][2],'#FFFFFF')
                tooltip = '%s <br> Intv: (%d, %d)' %(e[i][2], e[i][0], e[i][1])
                stack.append(bar_stack_value(val, colour, tooltip))
                
                if i != len(e) - 1:
                    # Add empty event after every event
                    val = e[i+1][0] - e[i][1]
                    colour  = event_codes['No_Event']
                    tooltip = '(%d, %d)' %(e[i][1], e[i+1][0])
                    stack.append(bar_stack_value(val, colour, tooltip))
            ind += 1
                   
            plot.append_stack(stack)
            
        chart = openFlashChart.template("ILP Video One", style = '{font-size: 20px; color: #F24062; text-align: center;}')
        chart.set_tooltip(behaviour = 'hover')
        chart.set_bg_colour('#FFFFFF')

        # Prepare x_lables
        xlabels = []
        for i in xrange(len(videos)):
            if i == 0:
                xlabels.append('GT')
            else:    
                xlabels.append('ins_' + repr(i))            
            
        chart.set_x_axis(labels = x_axis_labels(labels = xlabels))
        chart.set_y_axis(min = 0, max = 35000, steps = 500)
        chart.add_element(plot)

        return chart.encode()

    @cherrypy.expose
    def ilp_filtered_bar_stack_1(self):
        event_codes = {'GPU_Arrival':              '#FF6600',
                       'Handler_Deposites_Chocks': '#50284A',
                       'Aircraft_Arrival':         '#339900',
                       'Jet_Bridge_Positioning':   '#6699CC',
                       #'Container_Front_Unloading':'#660000',
                       #'Container_Front_Loading':  '#CC3333',
                       'Push_Back_Positioning':    '#FFF000',
                       #'Container_Back_Loading':   '#FF3333',
                       'Jet_Bridge_Parking':       '#0066CC',
                       'Aircraft_Departure':       '#99FF33',
                       'VRAC_Back_Unloading':      '#FF99FF',
                       #'Refuelling':               '#FF6600',
                       'VRAC_Back_Loading':        '#9933FF',
                       'No_Event':                 '#FFFFFF' 
                       }

        plot = Bar_Stack(colours = ['#C4D318', '#50284A', '#7D7B6A','#ff0000','#ff00ff'])
    
        for eve in event_codes:
            plot.append_keys(event_codes[eve], eve, 13)
        vid = 1
        # Get ground truth
        gt_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/global_model_ILP/' + 'ground_truth.p';     
        gt = pickle.load(open(gt_file))
        gt_event_lists = gt['event_lists']
        # Only add first video ground truth
        videos = [gt_event_lists[vid]]
        
        # Now the retrieved events
        ilp_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/new_gt_with_zone_1protos_oct/' + 'retrieved_ins_ILP_vis_filtered_events_1.p';
        re = pickle.load(open(ilp_file))
        re_event_ins_lists = re['event_lists']
        ind = 0
        for e in re_event_ins_lists:
            videos.append(e)
            ind += 1
            if ind > 7:
                break
                      
        ind = 0
        for e in videos:
            e.sort()
            # val for each strip in a stack is just the length of the strip.
            # So just keep on laying strips in the stack with length equal to length of interval
            # First start with empty event
            stack   = []            
            val     = e[0][0]
            colour  = event_codes['No_Event']
            tooltip = '(%d, %d)' %(0, e[0][0])
            stack.append(bar_stack_value(val, colour, tooltip))
        
            for i in range(len(e)):                
                val = e[i][1] - e[i][0]
                colour = event_codes.get(e[i][2],'#FFFFFF')
                tooltip = '%s <br> Intv: (%d, %d)' %(e[i][2], e[i][0], e[i][1])
                stack.append(bar_stack_value(val, colour, tooltip))
                
                if i != len(e) - 1:
                    # Add empty event after every event
                    val = e[i+1][0] - e[i][1]
                    colour  = event_codes['No_Event']
                    tooltip = '(%d, %d)' %(e[i][1], e[i+1][0])
                    stack.append(bar_stack_value(val, colour, tooltip))
            ind += 1
                   
            plot.append_stack(stack)
            
        chart = openFlashChart.template("ILP Video Two", style = '{font-size: 20px; color: #F24062; text-align: center;}')
        chart.set_tooltip(behaviour = 'hover')
        chart.set_bg_colour('#FFFFFF')

        # Prepare x_lables
        xlabels = []
        for i in xrange(len(videos)):
            if i == 0:
                xlabels.append('GT')
            else:    
                xlabels.append('ins_' + repr(i))            
            
        chart.set_x_axis(labels = x_axis_labels(labels = xlabels))
        chart.set_y_axis(min = 0, max = 35000, steps = 500)
        chart.add_element(plot)

        return chart.encode()

    @cherrypy.expose
    def ilp_filtered_bar_stack_2(self):
        event_codes = {'GPU_Arrival':              '#FF6600',
                       'Handler_Deposites_Chocks': '#50284A',
                       'Aircraft_Arrival':         '#339900',
                       'Jet_Bridge_Positioning':   '#6699CC',
                       #'Container_Front_Unloading':'#660000',
                       #'Container_Front_Loading':  '#CC3333',
                       'Push_Back_Positioning':    '#FFF000',
                       #'Container_Back_Loading':   '#FF3333',
                       'Jet_Bridge_Parking':       '#0066CC',
                       'Aircraft_Departure':       '#99FF33',
                       'VRAC_Back_Unloading':      '#FF99FF',
                       #'Refuelling':               '#FF6600',
                       'VRAC_Back_Loading':        '#9933FF',
                       'No_Event':                 '#FFFFFF' 
                       }

        plot = Bar_Stack(colours = ['#C4D318', '#50284A', '#7D7B6A','#ff0000','#ff00ff'])
    
        for eve in event_codes:
            plot.append_keys(event_codes[eve], eve, 13)
         
        vid = 2    
        # Get ground truth
        gt_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/global_model_ILP/' + 'ground_truth.p';     
        gt = pickle.load(open(gt_file))
        gt_event_lists = gt['event_lists']
        # Only add first video ground truth
        videos = [gt_event_lists[vid]]
        
        # Now the retrieved events
        ilp_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/new_gt_with_zone_1protos_oct/' + 'retrieved_ins_ILP_vis_filtered_events_2.p';
        re = pickle.load(open(ilp_file))
        re_event_ins_lists = re['event_lists']
        ind = 0
        for e in re_event_ins_lists:
            videos.append(e)
            ind += 1
            if ind > 7:
                break
                      
        ind = 0
        for e in videos:
            e.sort()
            # val for each strip in a stack is just the length of the strip.
            # So just keep on laying strips in the stack with length equal to length of interval
            # First start with empty event
            stack   = []            
            val     = e[0][0]
            colour  = event_codes['No_Event']
            tooltip = '(%d, %d)' %(0, e[0][0])
            stack.append(bar_stack_value(val, colour, tooltip))
        
            for i in range(len(e)):                
                val = e[i][1] - e[i][0]
                colour = event_codes.get(e[i][2],'#FFFFFF')
                tooltip = '%s <br> Intv: (%d, %d)' %(e[i][2], e[i][0], e[i][1])
                stack.append(bar_stack_value(val, colour, tooltip))
                
                if i != len(e) - 1:
                    # Add empty event after every event
                    val = e[i+1][0] - e[i][1]
                    colour  = event_codes['No_Event']
                    tooltip = '(%d, %d)' %(e[i][1], e[i+1][0])
                    stack.append(bar_stack_value(val, colour, tooltip))
            ind += 1
                   
            plot.append_stack(stack)
            
        chart = openFlashChart.template("ILP Video Three", style = '{font-size: 20px; color: #F24062; text-align: center;}')
        chart.set_tooltip(behaviour = 'hover')
        chart.set_bg_colour('#FFFFFF')

        # Prepare x_lables
        xlabels = []
        for i in xrange(len(videos)):
            if i == 0:
                xlabels.append('GT')
            else:    
                xlabels.append('ins_' + repr(i))            
            
        chart.set_x_axis(labels = x_axis_labels(labels = xlabels))
        chart.set_y_axis(min = 0, max = 35000, steps = 500)
        chart.add_element(plot)

        return chart.encode()
     
    @cherrypy.expose
    def ilp_filtered_bar_stack_3(self):
        event_codes = {'GPU_Arrival':              '#FF6600',
                       'Handler_Deposites_Chocks': '#50284A',
                       'Aircraft_Arrival':         '#339900',
                       'Jet_Bridge_Positioning':   '#6699CC',
                       #'Container_Front_Unloading':'#660000',
                       #'Container_Front_Loading':  '#CC3333',
                       'Push_Back_Positioning':    '#FFF000',
                       #'Container_Back_Loading':   '#FF3333',
                       'Jet_Bridge_Parking':       '#0066CC',
                       'Aircraft_Departure':       '#99FF33',
                       'VRAC_Back_Unloading':      '#FF99FF',
                       #'Refuelling':               '#FF6600',
                       'VRAC_Back_Loading':        '#9933FF',
                       'No_Event':                 '#FFFFFF' 
                       }

        plot = Bar_Stack(colours = ['#C4D318', '#50284A', '#7D7B6A','#ff0000','#ff00ff'])
    
        for eve in event_codes:
            plot.append_keys(event_codes[eve], eve, 13)

        vid = 3    
        # Get ground truth
        gt_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/global_model_ILP/' + 'ground_truth.p';     
        gt = pickle.load(open(gt_file))
        gt_event_lists = gt['event_lists']
        # Only add first video ground truth
        videos = [gt_event_lists[vid]]
        
        # Now the retrieved events
        ilp_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/new_gt_with_zone_1protos_oct/' + 'retrieved_ins_ILP_vis_filtered_events_3.p';
        re = pickle.load(open(ilp_file))
        re_event_ins_lists = re['event_lists']
        ind = 0
        for e in re_event_ins_lists:
            videos.append(e)
            ind += 1
            if ind > 7:
                break
                      
        ind = 0
        for e in videos:
            e.sort()
            # val for each strip in a stack is just the length of the strip.
            # So just keep on laying strips in the stack with length equal to length of interval
            # First start with empty event
            stack   = []            
            val     = e[0][0]
            colour  = event_codes['No_Event']
            tooltip = '(%d, %d)' %(0, e[0][0])
            stack.append(bar_stack_value(val, colour, tooltip))
        
            for i in range(len(e)):                
                val = e[i][1] - e[i][0]
                colour = event_codes.get(e[i][2],'#FFFFFF')
                tooltip = '%s <br> Intv: (%d, %d)' %(e[i][2], e[i][0], e[i][1])
                stack.append(bar_stack_value(val, colour, tooltip))
                
                if i != len(e) - 1:
                    # Add empty event after every event
                    val = e[i+1][0] - e[i][1]
                    colour  = event_codes['No_Event']
                    tooltip = '(%d, %d)' %(e[i][1], e[i+1][0])
                    stack.append(bar_stack_value(val, colour, tooltip))
            ind += 1
                   
            plot.append_stack(stack)
            
        chart = openFlashChart.template("ILP Video Four", style = '{font-size: 20px; color: #F24062; text-align: center;}')
        chart.set_tooltip(behaviour = 'hover')
        chart.set_bg_colour('#FFFFFF')

        # Prepare x_lables
        xlabels = []
        for i in xrange(len(videos)):
            if i == 0:
                xlabels.append('GT')
            else:    
                xlabels.append('ins_' + repr(i))            
            
        chart.set_x_axis(labels = x_axis_labels(labels = xlabels))
        chart.set_y_axis(min = 0, max = 35000, steps = 500)
        chart.add_element(plot)

        return chart.encode()

    @cherrypy.expose
    def ilp_filtered_bar_stack_vrac(self):
        event_codes = {'GPU_Arrival':              '#FF6600',
                       'Handler_Deposites_Chocks': '#50284A',
                       'Aircraft_Arrival':         '#339900',
                       'Jet_Bridge_Positioning':   '#6699CC',
                       #'Container_Front_Unloading':'#660000',
                       #'Container_Front_Loading':  '#CC3333',
                       'Push_Back_Positioning':    '#FFF000',
                       #'Container_Back_Loading':   '#FF3333',
                       'Jet_Bridge_Parking':       '#0066CC',
                       'Aircraft_Departure':       '#99FF33',
                       'VRAC_Back_Unloading':      '#FF99FF',
                       #'Refuelling':               '#FF6600',
                       'VRAC_Back_Loading':        '#9933FF',
                       'No_Event':                 '#AACCCC' 
                       }

        plot = Bar_Stack(colours = ['#C4D318', '#50284A', '#7D7B6A','#ff0000','#ff00ff'])
    
        for eve in event_codes:
            plot.append_keys(event_codes[eve], eve, 13)

        # Get ground truth
        gt_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/global_model_ILP/' + 'ground_truth.p';     
        gt = pickle.load(open(gt_file))
        gt_event_lists = gt['event_lists']
        # Only add first video ground truth
        videos = [gt_event_lists[2]]
        
        # Now the retrieved events
        ilp_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/global_model_ILP/' + 'retrieved_ins_ILP_vis_filtered_events_2.p';
        re = pickle.load(open(ilp_file))
        re_event_ins_lists = re['event_lists']
        ind = 0
        for e in re_event_ins_lists:
            videos.append(e)
            ind += 1
            if ind > 7:
                break
                      
        ind = 0
        for e in videos:
            e.sort()
            # val for each strip in a stack is just the length of the strip.
            # So just keep on laying strips in the stack with length equal to length of interval
            # First start with empty event
            stack   = []            
        
            for i in range(len(e)):                
                
                if e[i][2] != 'VRAC_Back_Loading':
                    continue
                if (26685 > e[i][0] and 26685 < e[i][1]) or (31066 > e[i][0] and 31066 < e[i][1]) or \
                    (26685 > e[i][0] and 31066 < e[i][1]):
                    val     = e[i][0]
                    colour  = event_codes['No_Event']
                    tooltip = '(%d, %d)' %(0, e[0][0])
                    stack.append(bar_stack_value(val, colour, tooltip))
                    val = e[i][1] - e[i][0]
                    colour = event_codes.get(e[i][2],'#FFFFFF')
                    tooltip = '%s <br> Intv: (%d, %d)' %(e[i][2], e[i][0], e[i][1])
                    stack.append(bar_stack_value(val, colour, tooltip))
                    
            plot.append_stack(stack)
            
        chart = openFlashChart.template("VRAC Event", style = '{font-size: 20px; color: #F24062; text-align: center;}')
        chart.set_tooltip(behaviour = 'hover')
        chart.set_bg_colour('#FFFFFF')

        # Prepare x_lables
        xlabels = []
        for i in xrange(len(videos)):
            xlabels.append('vid_' + repr(i))            
            
        chart.set_x_axis(labels = x_axis_labels(labels = xlabels))
        chart.set_y_axis(min = 0, max = 35000, steps = 500)
        chart.add_element(plot)

        return chart.encode()
    

    def source(self, filename):
        """Opens a file specified by the file/pathname in read-only"""
        file = open(filename, 'r')
        result = file.read()
        file.close()
        return result

    @cherrypy.expose
    def flashes(self, filename):
        cherrypy.response.headers['Content-Type'] = "application/x-shockwave-flash"
        cherrypy.response.headers['Expires'] = "Tue, 01 Dec 2009 12:00:00 GMT"
        cherrypy.response.headers['Cache-Control'] = "Public"
        return open(filename)


cherrypy.server.socket_host = socket.gethostbyname(socket.gethostname())
cherrypy.quickstart(OFC(), config = 'serverconfig.conf')

