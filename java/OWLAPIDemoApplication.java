import java.io.File;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import com.hp.hpl.jena.util.FileUtils;

import edu.stanford.smi.protege.exception.OntologyLoadException;
import edu.stanford.smi.protege.util.URIUtilities;
import edu.stanford.smi.protegex.owl.jena.JenaOWLModel;
import edu.stanford.smi.protegex.owl.model.NamespaceManager;
import edu.stanford.smi.protegex.owl.model.OWLAllValuesFrom;
import edu.stanford.smi.protegex.owl.model.OWLCardinality;
import edu.stanford.smi.protegex.owl.model.OWLDatatypeProperty;
import edu.stanford.smi.protegex.owl.model.OWLMinCardinality;
import edu.stanford.smi.protegex.owl.model.OWLModel;
import edu.stanford.smi.protegex.owl.model.OWLNamedClass;
import edu.stanford.smi.protegex.owl.model.OWLObjectProperty;
import edu.stanford.smi.protegex.owl.model.OWLUnionClass;
import edu.stanford.smi.protegex.owl.model.RDFSClass;
import edu.stanford.smi.protegex.owl.model.util.ImportHelper;
import edu.stanford.smi.protegex.owl.swrl.model.SWRLAtomList;
import edu.stanford.smi.protegex.owl.swrl.model.SWRLFactory;
import edu.stanford.smi.protegex.owl.swrl.model.SWRLImp;
import edu.stanford.smi.protegex.owl.swrl.parser.SWRLParseException;
import edu.stanford.smi.protegex.owl.ProtegeOWL;


public class OWLAPIDemoApplication {

    public static void main(String[] args) throws OntologyLoadException {
    	
        OWLModel owlModel = ProtegeOWL.createJenaOWLModel();
        
       /* NamespaceManager nsm = owlModel.getNamespaceManager();
        nsm.setDefaultNamespace("http://leeds.com/leeds1.owl#");
        nsm.setPrefix("http://leeds.com/leeds1.owl#", "leeds1");
     */
        //if you want to use a custom prefix for the namespace of the imported ontology, uncomment the following line
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
        
        OWLNamedClass vezClass  = owlModel.createOWLNamedSubclass("Vehicle-Enters-Zone", peClass);
        OWLNamedClass vlzClass  = owlModel.createOWLNamedSubclass("Vehicle-Leaves-Zone", peClass);
        OWLNamedClass vrClass   = owlModel.createOWLNamedSubclass("Vehicle-Removing", peClass);
        OWLNamedClass vsClass   = owlModel.createOWLNamedSubclass("Vehicle-Stopped", peClass);
        OWLNamedClass vizClass  = owlModel.createOWLNamedSubclass("Vehicle-Inside-Zone", peClass);
        OWLNamedClass vsizClass = owlModel.createOWLNamedSubclass("Vehicle-Stopped-Inside-Zone", peClass);       
        OWLNamedClass vpClass   = owlModel.createOWLNamedSubclass("Vehicle-Positioned", peClass);
        OWLNamedClass vpgClass  = owlModel.createOWLNamedSubclass("Vehicle-Positioning", peClass);

        OWLNamedClass mClass = owlModel.createOWLNamedSubclass("Mobile", poClass);
        OWLNamedClass zClass = owlModel.createOWLNamedSubclass("Zone", poClass);
        
        OWLNamedClass pClass = owlModel.createOWLNamedSubclass("Person", mClass);
        OWLNamedClass aClass = owlModel.createOWLNamedSubclass("Aircraft", mClass);        
        OWLNamedClass vClass = owlModel.createOWLNamedSubclass("Vehicle", mClass);
        
        OWLNamedClass hvClass  = owlModel.createOWLNamedSubclass("Heavy-Vehicle", vClass);
        OWLNamedClass lvClass  = owlModel.createOWLNamedSubclass("Light-Vehicle", vClass);
        OWLNamedClass tlvClass = owlModel.createOWLNamedSubclass("Transporter", lvClass);
        OWLNamedClass glvClass = owlModel.createOWLNamedSubclass("GPU", lvClass);
        OWLNamedClass lhvClass = owlModel.createOWLNamedSubclass("Loader", hvClass);
        OWLNamedClass bhvClass = owlModel.createOWLNamedSubclass("Bulk-Loader", hvClass);
        OWLNamedClass chvClass = owlModel.createOWLNamedSubclass("Conveyor-Belt", hvClass);
        OWLNamedClass phvClass = owlModel.createOWLNamedSubclass("Passenger-Stair", hvClass);
        OWLNamedClass mhvClass = owlModel.createOWLNamedSubclass("Mobile-Stair", hvClass);
        OWLNamedClass thvClass = owlModel.createOWLNamedSubclass("Tanker", hvClass);
        
        OWLNamedClass pzClass    = owlModel.createOWLNamedSubclass("Pbb-zone", zClass);
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
        
        OWLObjectProperty agProperty    = owlModel.createOWLObjectProperty("has-agent");
        OWLObjectProperty locProperty   = owlModel.createOWLObjectProperty("has-location");
        OWLObjectProperty partAProperty = owlModel.createOWLObjectProperty("has-part-A");
        OWLObjectProperty partBProperty = owlModel.createOWLObjectProperty("has-part-B");
        OWLObjectProperty partCProperty = owlModel.createOWLObjectProperty("has-part-C");
        OWLObjectProperty partDProperty = owlModel.createOWLObjectProperty("has-part-D");
                
        // Set domains for the properties
        agProperty.setDomain(mClass);
        locProperty.setDomain(zClass);
        partAProperty.setDomain(peClass);
        partBProperty.setDomain(peClass);
        partCProperty.setDomain(peClass);
        partDProperty.setDomain(peClass);
        
        Map<String, OWLNamedClass>     class_map     = new HashMap<String, OWLNamedClass>();
        Map<String, OWLObjectProperty> property_map  = new HashMap<String, OWLObjectProperty>();
        Map<String, List<Object>>      top_level_map = new HashMap<String, List<Object>>();
        
        property_map.put("has-agent", agProperty);
        property_map.put("has-location", locProperty);
        property_map.put("has-part-A", partAProperty);
        property_map.put("has-part-B", partBProperty);
        property_map.put("has-part-C", partCProperty);
        property_map.put("has-part-D", partDProperty);
        		
        class_map.put("Person", pClass);
        class_map.put("Veh", vClass);
        class_map.put("Aircraft", aClass);
        class_map.put("Heavy-veh", hvClass);
        class_map.put("Light-veh", lvClass);
        class_map.put("Transporter", tlvClass);
        class_map.put("Ground-power-unit", glvClass);
        class_map.put("Loader", lhvClass);
        class_map.put("Bulk-loader", bhvClass);
        class_map.put("Conveyor-belt", chvClass);
        class_map.put("Passenger-stair", phvClass);
        class_map.put("Mobile-stair", mhvClass);
        class_map.put("Tanker", thvClass);
        
        class_map.put("Vehicle-Enters-Zone", vezClass);
        class_map.put("Vehicle-Leaves-Zone", vlzClass);
        class_map.put("Vehicle-Removing", vrClass);
        class_map.put("Vehicle-Stopped", vsClass);
        class_map.put("Vehicle-Inside-Zone", vizClass);
        class_map.put("Vehicle-Stopped-Inside-Zone", vsizClass);
        class_map.put("Vehicle-Positioned", vpClass);
        class_map.put("Vehicle-Positioning", vpgClass);
        
        class_map.put("Pbb-zone", pzClass); 
        class_map.put("Left-tk-zone", ltzClass);
        class_map.put("Left-fwd-pd-zone", lfpzClass);
        class_map.put("Left-aft-pd-zone", lapzClass);
        class_map.put("Right-aft-pd-zone", rapzClass); 
        class_map.put("Right-aft-ts-zone", ratzClass);
        class_map.put("Right-aft-bulk-ts-zone", rabtzClass);
        class_map.put("Right-aft-bl-zone", rabzClass);
        class_map.put("Right-aft-ld-zone", ralzClass);
        class_map.put("Right-fwd-ld-zone", rflzClass);
        class_map.put("Right-fwd-pd-zone", rfpzClass);
        class_map.put("Right-fwd-ts-zone", rftzClass);
        class_map.put("Gpu-zone", gzClass);        	
        class_map.put("Departure-zone", dzClass);
        class_map.put("Arrival-zone", azClass);
        
        //Importing the constraints.owl. First create the ImportHelper. 
        //The prefix names are automatically assigned like allen, constraints etc.
		ImportHelper importHelper = new ImportHelper((JenaOWLModel)owlModel);

		//this is the URI from where your ontology is created 
		URI importUri = URIUtilities.createURI("/home/csunix/scksrd/Documents/cofriend/data/owl/constraints.owl");
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
   	  
        File folder = new File("/home/csunix/visdata/cofriend/data/ilp/sep/inria_data/par16_type_dur/owl/");
        File[] listOfFiles = folder.listFiles();

        SWRLFactory factory = new SWRLFactory(owlModel);
        
        for (int i = 0; i < listOfFiles.length; i++) {
          if (listOfFiles[i].isFile()) {
        	  hyp2owl2 dpe = new hyp2owl2(listOfFiles[i].getAbsolutePath());
         	  //call run example
      		  NewHyp hyp = dpe.getHypFromXML();
      		  String hyp_id = hyp.getId();
              String swrl = hyp.getSwrl();
              String parent_event = swrl.split("::")[0];
              String swrl_rule = swrl.split("::")[1];
         	  String event = parent_event;         	  
         	  OWLNamedClass aeClass;
              if (Integer.parseInt(hyp_id.trim()) != 0){
            	  event = event + hyp_id;
            	  aeClass = owlModel.createOWLNamedSubclass(event, ceClass);        
              }
              else {
            	  event = event + hyp_id;
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
              System.out.println(swrl_rule);
              try {
		          //SWRLImp imp = factory.createImp("Age_Rule", "Person(?p) ^ hasAge(?p, ?age) ^ swrlb:greaterThan(?age, 17) -> Adult(?p)");
                  SWRLImp imp = factory.createImp(event + "-Rule", swrl_rule);
		          //SWRLImp imp2 = factory.createImp("Aircraft-Arrival2-Rule", "Aircraft-Arrival(?e) ^ has-part-A(?e, ?e1) ^ has-part-B(?e, ?e2) ^ Aircraft(?v) ^ Arrival-Zone(?z) ^ Vehicle-Inside-Zone(?e1) ^ has-agent(?e1, ?v) ^ has-location(?e1, ?z) ^ Vehicle-Positioning(?e2) ^ has-agent(?e2, ?v) ^ has-location(?e2, ?z) -> allen:before(?e1, ?e2)");
		      	  //System.out.println(imp);
	      	  } catch (SWRLParseException e) {
	      		  // TODO Auto-generated catch block
	      		  e.printStackTrace();
	      	  } 
	              
      		  // Add conditions like 'has-part-A' etc to this class
              
              //OWLCardinality cardinality1 = owlModel.createOWLCardinality(partAProperty, 1, vizClass);
              //OWLCardinality cardinality2 = owlModel.createOWLCardinality(partBProperty, 1, vsClass);
              //OWLAllValuesFrom subRestriction = owlModel.createOWLAllValuesFrom(partAProperty, vizClass);
              //aaClass.addSuperclass(subRestriction);
              //aaClass1.addSuperclass(cardinality1);
              //aaClass1.addSuperclass(cardinality2);
           /*   
              OWLNamedClass aaClass2 = owlModel.createOWLNamedSubclass("Aircraft-Arrival2", ceClass);
              OWLCardinality cardinality3 = owlModel.createOWLCardinality(partAProperty, 1, vizClass);
              OWLCardinality cardinality4 = owlModel.createOWLCardinality(partBProperty, 1, vpgClass);
              //OWLAllValuesFrom subRestriction = owlModel.createOWLAllValuesFrom(partAProperty, vizClass);
              //aaClass.addSuperclass(subRestriction);
              aaClass2.addSuperclass(cardinality3);
              aaClass2.addSuperclass(cardinality4);
              
              OWLUnionClass unionClass = owlModel.createOWLUnionClass();
              unionClass.addOperand(aaClass1);
              unionClass.addOperand(aaClass2);
              OWLNamedClass aaClass = owlModel.createOWLNamedSubclass("Aircraft-Arrival", ceClass);
              aaClass.addSuperclass(unionClass);
	      		*/
              
	          
              /*SWRLAtomList body = factory.createSWRLAtomList()
              SWRLAtomList head = factory.createSWRLAtomList();
              SWRLImp imp = factory.createImp(body, head);*/
      		
          } else if (listOfFiles[i].isDirectory()) {
            System.out.println("Directory " + listOfFiles[i].getName());
          }
        }
        
        Iterator it = top_level_map.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry pairs = (Map.Entry)it.next();
            OWLNamedClass aeClass = owlModel.createOWLNamedSubclass((String) pairs.getKey(), ceClass);
            OWLUnionClass unionClass = owlModel.createOWLUnionClass();
            List<Object> sub_events = (List<Object>) pairs.getValue();
            for(Object obj : sub_events) {
            	unionClass.addOperand((OWLNamedClass) obj);
            }
            aeClass.addSuperclass(unionClass);         
        }
 
        String fileName = "/home/csunix/scksrd/Documents/cofriend/data/owl/lam_ontology2.owl";
        Collection errors = new ArrayList();

        ((JenaOWLModel) owlModel).save(new File(fileName).toURI(), FileUtils.langXMLAbbrev, errors);
        System.out.println("File saved with " + errors.size() + " errors.");
    }
}
