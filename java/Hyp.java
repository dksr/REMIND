import java.util.Map;


public class Hyp {
	private String swrl_rule;

	private String id;
	
	private  Map<String, String> conditions;
	
	public Hyp(){		
	}
	
	public Hyp(String swrl, Map<String, String> m, String id){
		this.conditions = m;
		this.swrl_rule  = swrl;
		this.id = id;
	}
	
	public String getSwrl(){
		return this.swrl_rule;
	}
	
	public void setSwrl(String rule){
		this.swrl_rule = rule;
	}
	
	public Map<String, String> getConditions(){
		return this.conditions;
	}
	
	public void setConditions(Map<String, String> conds){
		this.conditions = conds;
	}
	
	public String getId(){
		return this.id;
	}
	
	public void setId(String id){
		this.id = id;
	}
	public String toString(){
		return this.conditions.toString() + this.swrl_rule;
	}
}
