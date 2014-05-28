import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.CharacterData;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

public class Xml2Hyp {

	//No generics
	Document dom;
	Hyp e;
	String xml_file;

	public Xml2Hyp(String xmlfile){
		xml_file = xmlfile;
	}

	public Hyp getHypFromXML() {
		
		//parse the xml file and get the dom object
		parseXmlFile();
		
		//get each employee element and create a Employee object
		this.e = parseHyp();
		//Iterate through the list and print the data
		//printData();
		return this.e;
		
	}
	
	private void parseXmlFile(){
		//get the factory
		DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
		
		try {
			
			//Using factory get an instance of document builder
			DocumentBuilder db = dbf.newDocumentBuilder();
			
			//parse using builder to get DOM representation of the XML file
			dom = db.parse(xml_file);
			

		}catch(ParserConfigurationException pce) {
			pce.printStackTrace();
		}catch(SAXException se) {
			se.printStackTrace();
		}catch(IOException ioe) {
			ioe.printStackTrace();
		}
	}
	
	private Hyp parseHyp(){
		//get the root elememt
		Element docEle = dom.getDocumentElement();
		Hyp e = getHyp(docEle);
		return e;
	}

	public static String getCharacterDataFromElement(Element e) {
		   Node child = e.getFirstChild();
		   if (child instanceof CharacterData) {
		     CharacterData cd = (CharacterData) child;
		       return cd.getData();
		     }
		   System.out.println("Not char data");
		   return "?";
    }

	/**
	 * I take an employee element and read the values in, create
	 * an Employee object and return it
	 * @param empEl
	 * @return
	 */
	private Hyp getHyp(Element empEl) {
		
		Map<String, String> m = new HashMap<String, String>();

		NodeList hypNodeList = empEl.getElementsByTagName("id");
		Element idclass = (Element) hypNodeList.item(0);
		String id = getCharacterDataFromElement(idclass);	
		String swrl;
		NodeList empElLst = empEl.getElementsByTagName("owlclass");
		Element owlclass = (Element) empElLst.item(0);
		NodeList owlLst = owlclass.getElementsByTagName("conditions");
		Element cond = (Element) owlLst.item(0);
		NodeList condList = cond.getElementsByTagNameNS("*", "*");
		if(condList != null && condList.getLength() > 0) {
			for(int i = 0 ; i <condList.getLength();i++) {
				String name = condList.item(i).getNodeName();
				Element el = (Element)condList.item(i);
				String prim_event = getCharacterDataFromElement(el);
				prim_event = prim_event.replace( '_', '-' );
				prim_event = prim_event.substring(0,1).toUpperCase() + prim_event.substring(1);
				m.put(name, prim_event);
			}
		}
		NodeList swrlLst = empEl.getElementsByTagName("swrl");
		Element swrl_ele = (Element) swrlLst.item(0);
		String swrl_name = swrl_ele.getAttribute("name");
		String swrl_rule = swrl_ele.getAttribute("value");
		swrl_name = swrl_name.replace( '_', '-' );
		swrl_rule = swrl_rule.replace( '_', '-' );
		swrl_name = swrl_name.substring(0,1).toUpperCase() + swrl_name.substring(1);
		swrl_rule = swrl_rule.substring(0,1).toUpperCase() + swrl_rule.substring(1);
		swrl = swrl_name + "::" + swrl_rule;
		Hyp e = new Hyp(swrl, m, id);
		return e;
	}

	/**
	 * Iterate through the list and print the 
	 * content to console
	 */
	private void printData(){
		System.out.println(e.toString());
	}

	
	public static void main(String[] args){
		//create an instance
		String xmlfile = "/home/csunix/scksrd/Documents/cofriend/data/owl/hyp2.xml";
		Xml2Hyp dpe = new Xml2Hyp(xmlfile);
		
		//call run example
		dpe.getHypFromXML();
	}

}
