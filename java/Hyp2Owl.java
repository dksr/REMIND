/*
 * java -jar hyp2owl.jar constraints_file.owl owl_xml_dir output_owl_file_name 
 * Make sure output file is not stored in owl_xml_dir. This will create parse problems.
 */

import java.io.File;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.lang.Boolean;

import com.hp.hpl.jena.util.FileUtils;

import edu.stanford.smi.protege.exception.OntologyLoadException;
import edu.stanford.smi.protege.util.URIUtilities;
import edu.stanford.smi.protegex.owl.jena.JenaOWLModel;
import edu.stanford.smi.protegex.owl.model.OWLCardinality;
import edu.stanford.smi.protegex.owl.model.OWLDatatypeProperty;
import edu.stanford.smi.protegex.owl.model.OWLHasValue;
import edu.stanford.smi.protegex.owl.model.OWLModel;
import edu.stanford.smi.protegex.owl.model.OWLNamedClass;
import edu.stanford.smi.protegex.owl.model.OWLObjectProperty;
import edu.stanford.smi.protegex.owl.model.OWLUnionClass;
import edu.stanford.smi.protegex.owl.model.util.ImportHelper;
import edu.stanford.smi.protegex.owl.swrl.model.SWRLFactory;
import edu.stanford.smi.protegex.owl.swrl.model.SWRLImp;
import edu.stanford.smi.protegex.owl.swrl.parser.SWRLParseException;
import edu.stanford.smi.protegex.owl.ProtegeOWL;

public class Hyp2Owl {

    public static void main(String[] args) throws OntologyLoadException {
    	int args_length = args.length;
    	String constraints_file;
    	String output_owl_file;
    	String input_xml_dir;
    	
    	if (args_length == 0) {
    		constraints_file = "/home/csunix/scksrd/Documents/cofriend/data/owl/constraints.owl";
    		input_xml_dir    = "/home/csunix/visdata/cofriend/data/ilp/sep/inria_data/par16_type_dur/owl/";
    		output_owl_file  = "/home/csunix/scksrd/Documents/cofriend/data/owl/lam_ontology.owl";
    	}
    	else {
    		constraints_file = args[0];
    		input_xml_dir    = args[1];
    		output_owl_file  = args[2];
    	}
    	
        OWLModel owlModel = ProtegeOWL.createJenaOWLModel();
        
    	try {
			owlModel.getNamespaceManager().setPrefix(new URI("http://www.owl-ontologies.com/Ontology1284131071.owl#"), "leeds");
		} catch (URISyntaxException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		
        OWLNamedClass soClass = owlModel.createOWLNamedClass("Scene-Object");
        OWLNamedClass coClass = owlModel.createOWLNamedSubclass("Conceptual-Object", soClass);
        OWLNamedClass poClass = owlModel.createOWLNamedSubclass("Physical-Object", soClass);
        OWLNamedClass eClass  = owlModel.createOWLNamedSubclass("Event", coClass);
        OWLNamedClass ceClass = owlModel.createOWLNamedSubclass("Composite-Event", eClass);
        OWLNamedClass peClass = owlModel.createOWLNamedSubclass("Primitive-Event", eClass);
        
        OWLNamedClass taClass = owlModel.createOWLNamedSubclass("Turn-Around", ceClass);
        
        OWLNamedClass mClass = owlModel.createOWLNamedSubclass("Mobile", poClass);
        OWLNamedClass zClass = owlModel.createOWLNamedSubclass("Zone", poClass);
        
        OWLNamedClass pClass = owlModel.createOWLNamedSubclass("Person", mClass);
        //OWLNamedClass aClass = owlModel.createOWLNamedSubclass("Aircraft", mClass);        
        OWLNamedClass vClass = owlModel.createOWLNamedSubclass("Vehicle", mClass);
        
        OWLNamedClass hvClass    = owlModel.createOWLNamedSubclass("Heavy-Vehicle", vClass);
        OWLNamedClass lvClass    = owlModel.createOWLNamedSubclass("Light-Vehicle", vClass);
        OWLNamedClass tlvClass   = owlModel.createOWLNamedSubclass("Transporter", lvClass);
        OWLNamedClass glvClass   = owlModel.createOWLNamedSubclass("GPU", lvClass);
        OWLNamedClass lhvClass   = owlModel.createOWLNamedSubclass("Loader", hvClass);
        OWLNamedClass bhvClass   = owlModel.createOWLNamedSubclass("Bulk-Loader", hvClass);
        OWLNamedClass chvClass   = owlModel.createOWLNamedSubclass("Conveyor-Belt", hvClass);
        OWLNamedClass phvClass   = owlModel.createOWLNamedSubclass("Passenger-Stair", hvClass);
        OWLNamedClass mhvClass   = owlModel.createOWLNamedSubclass("Mobile-Stair", hvClass);
        OWLNamedClass thvClass   = owlModel.createOWLNamedSubclass("Tanker", hvClass);
        OWLNamedClass svlvClass  = owlModel.createOWLNamedSubclass("Service-vehicle", lvClass);
        OWLNamedClass  pblvClass = owlModel.createOWLNamedSubclass("Push-back", lvClass);
        OWLNamedClass pbbhvClass = owlModel.createOWLNamedSubclass("Passenger-boarding-bridge", hvClass);
        OWLNamedClass cthvClass  = owlModel.createOWLNamedSubclass("Container", hvClass);
        OWLNamedClass cathvClass = owlModel.createOWLNamedSubclass("Catering", hvClass);
        // Making aircraft as heavy vehicle
        OWLNamedClass aClass     = owlModel.createOWLNamedSubclass("Aircraft", hvClass);
        
        OWLNamedClass ezClass    = owlModel.createOWLNamedSubclass("Era", zClass);
        OWLNamedClass pbzClass   = owlModel.createOWLNamedSubclass("Pb-zone", zClass);
        OWLNamedClass pbbzClass  = owlModel.createOWLNamedSubclass("Pbb-zone", zClass);
        OWLNamedClass ltzClass   = owlModel.createOWLNamedSubclass("Left-tk-zone", zClass);
        OWLNamedClass lfpzClass  = owlModel.createOWLNamedSubclass("Left-fwd-pd-zone", zClass);
        OWLNamedClass lapzClass  = owlModel.createOWLNamedSubclass("Left-aft-pd-zone", zClass);
        OWLNamedClass rapzClass  = owlModel.createOWLNamedSubclass("Right-aft-pd-zone", zClass);
        OWLNamedClass ratzClass  = owlModel.createOWLNamedSubclass("Right-aft-ts-zone", zClass);
        OWLNamedClass rabtzClass = owlModel.createOWLNamedSubclass("Right-aft-bulk-ts-zone", zClass);
        OWLNamedClass rabzClass  = owlModel.createOWLNamedSubclass("Right-aft-bl-zone", zClass);
        OWLNamedClass ralzClass  = owlModel.createOWLNamedSubclass("Right-aft-ld-zone", zClass);
        OWLNamedClass rflzClass  = owlModel.createOWLNamedSubclass("Right-fwd-ld-zone", zClass);
        OWLNamedClass rfpzClass  = owlModel.createOWLNamedSubclass("Right-fwd-pd-zone", zClass);
        OWLNamedClass rftzClass  = owlModel.createOWLNamedSubclass("Right-fwd-ts-zone", zClass);
        OWLNamedClass gzClass    = owlModel.createOWLNamedSubclass("Gpu-zone", zClass);
        OWLNamedClass dzClass    = owlModel.createOWLNamedSubclass("Departure-zone", zClass);
        OWLNamedClass azClass    = owlModel.createOWLNamedSubclass("Arrival-zone", zClass);
        OWLNamedClass jzClass    = owlModel.createOWLNamedSubclass("Jet-bridge-evolution", zClass);
        
        // Necessary for SCENIOR to independently work with events irrespective of context 
        OWLDatatypeProperty contextProperty = owlModel.createOWLDatatypeProperty("is-context-free");
  
        OWLObjectProperty agProperty    = owlModel.createOWLObjectProperty("has-agent");
        OWLObjectProperty locProperty   = owlModel.createOWLObjectProperty("has-location");
        OWLObjectProperty partAProperty = owlModel.createOWLObjectProperty("has-part-A");
        OWLObjectProperty partBProperty = owlModel.createOWLObjectProperty("has-part-B");
        OWLObjectProperty partCProperty = owlModel.createOWLObjectProperty("has-part-C");
        OWLObjectProperty partDProperty = owlModel.createOWLObjectProperty("has-part-D");
        OWLObjectProperty partEProperty = owlModel.createOWLObjectProperty("has-part-E");
        OWLObjectProperty partFProperty = owlModel.createOWLObjectProperty("has-part-F");
        OWLObjectProperty partGProperty = owlModel.createOWLObjectProperty("has-part-G");
        OWLObjectProperty partHProperty = owlModel.createOWLObjectProperty("has-part-H");
        OWLObjectProperty partIProperty = owlModel.createOWLObjectProperty("has-part-I");
        OWLObjectProperty partJProperty = owlModel.createOWLObjectProperty("has-part-J");
        OWLObjectProperty partKProperty = owlModel.createOWLObjectProperty("has-part-K");
        OWLObjectProperty partLProperty = owlModel.createOWLObjectProperty("has-part-L");
        OWLObjectProperty partMProperty = owlModel.createOWLObjectProperty("has-part-M");
        OWLObjectProperty partNProperty = owlModel.createOWLObjectProperty("has-part-N");
        OWLObjectProperty partOProperty = owlModel.createOWLObjectProperty("has-part-O");
        OWLObjectProperty partPProperty = owlModel.createOWLObjectProperty("has-part-P");
        OWLObjectProperty partQProperty = owlModel.createOWLObjectProperty("has-part-Q");
      
        OWLNamedClass vezClass  = owlModel.createOWLNamedSubclass("Vehicle-Enters-Zone", peClass);
        OWLNamedClass vlzClass  = owlModel.createOWLNamedSubclass("Vehicle-Leaves-Zone", peClass);
        OWLNamedClass vrClass   = owlModel.createOWLNamedSubclass("Vehicle-Removing", peClass);
        OWLNamedClass vsClass   = owlModel.createOWLNamedSubclass("Vehicle-Stopped", peClass);
        OWLNamedClass vizClass  = owlModel.createOWLNamedSubclass("Vehicle-Inside-Zone", peClass);
        OWLNamedClass vsizClass = owlModel.createOWLNamedSubclass("Vehicle-Stopped-Inside-Zone", peClass);       
        OWLNamedClass vpClass   = owlModel.createOWLNamedSubclass("Vehicle-Positioned", peClass);
        OWLNamedClass vpgClass  = owlModel.createOWLNamedSubclass("Vehicle-Positioning", peClass);

        // These are added to primitive events
        OWLCardinality ag_cardinality  = owlModel.createOWLCardinality(agProperty, 1, mClass);
        OWLCardinality loc_cardinality = owlModel.createOWLCardinality(locProperty, 1, zClass);
        
        // Add agent and location properties to primitive events. Vehicle_Stopped does not have loc property 
        vezClass.addSuperclass(ag_cardinality);
        vezClass.addSuperclass(loc_cardinality);
        vlzClass.addSuperclass(ag_cardinality);
        vlzClass.addSuperclass(loc_cardinality);
        vrClass.addSuperclass(ag_cardinality);
        vrClass.addSuperclass(loc_cardinality);
        vsClass.addSuperclass(ag_cardinality);
        vizClass.addSuperclass(ag_cardinality);
        vizClass.addSuperclass(loc_cardinality);
        vsizClass.addSuperclass(ag_cardinality);
        vsizClass.addSuperclass(loc_cardinality);
        vpClass.addSuperclass(ag_cardinality);
        vpClass.addSuperclass(loc_cardinality);
        vpgClass.addSuperclass(ag_cardinality);
        vpgClass.addSuperclass(loc_cardinality);
                
        List<OWLObjectProperty> prop_list = new ArrayList<OWLObjectProperty>();
        prop_list.add(partEProperty);
        prop_list.add(partFProperty);
        prop_list.add(partGProperty);
        prop_list.add(partHProperty);
        prop_list.add(partIProperty);
        prop_list.add(partJProperty);
        prop_list.add(partKProperty);
        prop_list.add(partLProperty);
        prop_list.add(partMProperty);
        prop_list.add(partNProperty);
        prop_list.add(partOProperty);
        prop_list.add(partPProperty);
        prop_list.add(partQProperty);
        
        // Set domains for the properties
        agProperty.setDomain(mClass);
        locProperty.setDomain(zClass);
        partAProperty.setDomain(peClass);
        partBProperty.setDomain(peClass);
        partCProperty.setDomain(peClass);
        partDProperty.setDomain(peClass);
        partEProperty.setDomain(ceClass);
        partFProperty.setDomain(ceClass);
        partGProperty.setDomain(ceClass);
        partHProperty.setDomain(ceClass);
        partIProperty.setDomain(ceClass);
        partJProperty.setDomain(ceClass);
        partKProperty.setDomain(ceClass);
        partLProperty.setDomain(ceClass);
        partMProperty.setDomain(ceClass);
        partNProperty.setDomain(ceClass);
        partOProperty.setDomain(ceClass);
        partPProperty.setDomain(ceClass);
        partQProperty.setDomain(ceClass);
        
        Map<String, OWLNamedClass>     class_map     = new HashMap<String, OWLNamedClass>();
        Map<String, List<Object>>      top_level_map = new HashMap<String, List<Object>>();
        Map<String, OWLObjectProperty> property_map  = new HashMap<String, OWLObjectProperty>();
        
        property_map.put("has-agent", agProperty);
        property_map.put("has-location", locProperty);
        property_map.put("has-part-A", partAProperty);
        property_map.put("has-part-B", partBProperty);
        property_map.put("has-part-C", partCProperty);
        property_map.put("has-part-D", partDProperty);
        		
        class_map.put("Obj", poClass);
        class_map.put("Person", pClass);
        class_map.put("Veh", vClass);
        class_map.put("Aircraft", aClass);
        class_map.put("Heavy-veh", hvClass);
        class_map.put("Light-veh", lvClass);
        class_map.put("Service-vehicle", svlvClass);
        class_map.put("Push-back", pblvClass);
        class_map.put("Passenger-boarding-bridge", pbbhvClass);
        class_map.put("Container", cthvClass);
        class_map.put("Catering", cathvClass);
        class_map.put("Transporter", tlvClass);
        class_map.put("Ground-power-unit", glvClass);
        class_map.put("Conveyor-belt", chvClass);
        class_map.put("Loader", lhvClass);
        class_map.put("Bulk-loader", bhvClass);
        class_map.put("Tanker", thvClass);
        class_map.put("Passenger-stair", phvClass);
        class_map.put("Mobile-stair", mhvClass);        
         
        class_map.put("Vehicle-Enters-Zone", vezClass);
        class_map.put("Vehicle-Leaves-Zone", vlzClass);
        class_map.put("Vehicle-Removing", vrClass);
        class_map.put("Vehicle-Stopped", vsClass);
        class_map.put("Vehicle-Inside-Zone", vizClass);
        class_map.put("Vehicle-Positioned", vpClass);
        class_map.put("Vehicle-Positioning", vpgClass);
        class_map.put("Vehicle-Stopped-Inside-Zone", vsizClass);
        
        class_map.put("Era",                    ezClass);
        class_map.put("Gpu-zone",               gzClass);        	
        class_map.put("Departure-zone",         dzClass);
        class_map.put("Arrival-zone",           azClass);
        class_map.put("Pb-zone",                pbzClass);
        class_map.put("Pbb-zone",               pbbzClass); 
        class_map.put("Left-tk-zone",           ltzClass);
        class_map.put("Left-fwd-pd-zone",       lfpzClass);
        class_map.put("Left-aft-pd-zone",       lapzClass);
        class_map.put("Right-fwd-ld-zone",      rflzClass);
        class_map.put("Right-fwd-pd-zone",      rfpzClass);
        class_map.put("Right-fwd-ts-zone",      rftzClass);        
        class_map.put("Right-aft-pd-zone",      rapzClass); 
        class_map.put("Right-aft-ts-zone",      ratzClass);
        class_map.put("Right-aft-bl-zone",      rabzClass);
        class_map.put("Right-aft-ld-zone",      ralzClass);
        class_map.put("Right-aft-bulk-ts-zone", rabtzClass);
        class_map.put("Jet-bridge-evolution",   jzClass);
        
        
        List<OWLNamedClass> primitive_event_list = new ArrayList<OWLNamedClass>();
        primitive_event_list.add(vezClass);
        primitive_event_list.add(vlzClass);
        primitive_event_list.add(vrClass);
        primitive_event_list.add(vsClass);
        primitive_event_list.add(vizClass);
        primitive_event_list.add(vsizClass);
        primitive_event_list.add(vpClass);
        primitive_event_list.add(vpgClass);
        
              
        //Importing the constraints.owl. First create the ImportHelper. 
        //The prefix names are automatically assigned like allen, constraints etc.
		ImportHelper importHelper = new ImportHelper((JenaOWLModel)owlModel);

		File cf = new File(constraints_file);        
        boolean exists = cf.exists();
	    if (!exists) {
	    	System.out.println("ERROR: " + constraints_file + " is MISSING ");
	    	System.exit(1);
		}
	    
	    File xml_folder = new File(input_xml_dir);        
        exists = xml_folder.exists();
	    if (!exists) {
	    	System.out.println("ERROR: " + input_xml_dir + " is MISSING ");
	    	System.exit(1);
		}
	    
		//this is the URI from where your ontology is created
		URI importUri = URIUtilities.createURI(constraints_file);
		// Store concepts in an owl file and import it like this
		//URI importUri2 = URIUtilities.createURI("/home/csunix/scksrd/Documents/cofriend/data/owl/aa_swrl.owl");
		//add the import (multiple imports can be added here)
		importHelper.addImport(importUri);
		//importHelper.addImport(importUri2);
		
		try {
   		    //do the actual import
   		    importHelper.importOntologies(false);
   		    System.out.println("Loaded constraints.owl");
   	    } catch (Exception e) {		
   		    e.printStackTrace();
   	    }
   	       	    
        File[] listOfFiles = xml_folder.listFiles();

        SWRLFactory factory  = new SWRLFactory(owlModel);
        OWLHasValue hasValue = owlModel.createOWLHasValue(contextProperty, Boolean.TRUE);
        for (int i = 0; i < listOfFiles.length; i++) {
          if (listOfFiles[i].isFile()) {
        	  System.out.println(listOfFiles[i].getAbsolutePath());
        	  Xml2Hyp dpe = new Xml2Hyp(listOfFiles[i].getAbsolutePath());
         	  //call run example
      		  Hyp hyp    = dpe.getHypFromXML();
      		  String hyp_id = hyp.getId();
              String swrl   = hyp.getSwrl();
              String parent_event = swrl.split("::")[0];
              String swrl_rule    = swrl.split("::")[1];
         	  String event        = parent_event;         	  
         	  OWLNamedClass aeClass;
              if (Integer.parseInt(hyp_id.trim()) != 0){
            	  event   = event + hyp_id;
            	  aeClass = owlModel.createOWLNamedSubclass(event, ceClass);        
              }
              else {
            	  event   = event + hyp_id;
            	  aeClass = owlModel.createOWLNamedSubclass(event, ceClass);
            	  top_level_map.put(parent_event, new ArrayList<Object>());
              }
        	  List<Object> temp_list = top_level_map.get(parent_event);
        	  temp_list.add(aeClass);
        	  top_level_map.put(parent_event, temp_list);
              
              Map conds = hyp.getConditions();
              Iterator it = conds.entrySet().iterator();
              while (it.hasNext()) {
                  Map.Entry pairs = (Map.Entry)it.next();
                  OWLCardinality cardinality = owlModel.createOWLCardinality(property_map.get(pairs.getKey()), 1, class_map.get(pairs.getValue()));
                  aeClass.addSuperclass(cardinality);
                  System.out.println(pairs.getKey() + " = " + pairs.getValue());
              }
              System.out.println("Event: " + event);
              System.out.println("SWRL rule: " + swrl_rule);
              try {
		          SWRLImp imp = factory.createImp(event + "-Rule", swrl_rule);
		  	  } catch (SWRLParseException e) {
	      		  // TODO Auto-generated catch block
	      		  e.printStackTrace();
	      	  }              
		  	  // Add "is-context-free" property
              aeClass.addSuperclass(hasValue);
          
          } else if (listOfFiles[i].isDirectory()) {
            System.out.println("Directory " + listOfFiles[i].getName());
          }
        }
        
        /*Create top level 'Turn Around' event with all other events as parts*/
        Iterator it = top_level_map.entrySet().iterator();
        int j = 0;
        while (it.hasNext()) {
            Map.Entry pairs = (Map.Entry)it.next();
            OWLNamedClass aeClass    = owlModel.createOWLNamedSubclass((String) pairs.getKey(), ceClass);
            OWLUnionClass unionClass = owlModel.createOWLUnionClass();
            List<Object> sub_events  = (List<Object>) pairs.getValue();
            for(Object obj : sub_events) {
            	unionClass.addOperand((OWLNamedClass) obj);
            }
            aeClass.addSuperclass(unionClass);
      	    // Add "is-context-free" property
            aeClass.addSuperclass(hasValue);
            OWLCardinality cardinality = owlModel.createOWLCardinality(prop_list.get(j), 1, aeClass);
            taClass.addSuperclass(cardinality);
            j = j + 1;
        }
        
        String fileName   = output_owl_file;
        Collection errors = new ArrayList();

        ((JenaOWLModel) owlModel).save(new File(fileName).toURI(), FileUtils.langXMLAbbrev, errors);
        System.out.println("File saved with " + errors.size() + " errors.");
    }
}
