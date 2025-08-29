#!/usr/bin/env python3

import json
import sys
from datetime import datetime

def main():
    
    # Default question if the petition doesn't have argument
    question = sys.argv[2] if len(sys.argv) > 1 else "percent change"
    response = sys.argv[1]
        
    try:
        # Call Data
        #response = requests.get("http://n8n:5678/webhook-test/api")
        data = json.loads(response)
        
        # Transform to human lenguage
        if "error" in data:
            return f"Error getting data: {data['error']}"
        
        answer = "Marketing Performance Analysis"
        
        # Summary
        if "kpi_comparison" in data:
            s_cac = data.get("kpi_comparison", [{}])[0]
            s_roas = data.get("kpi_comparison", [{}])[1]
            answer += "**Key Metrics:**"
            answer += f"• last_30_days CAC: ${s_cac.get('last_30_days', 'N/A')}"
            answer += f"• last_30_days ROAS: {s_roas.get('last_30_days', 'N/A')}x"
            answer += f"• prior_30_days CAC: ${s_cac.get('prior_30_days', 'N/A')}"
            answer += f"• prior_30_days ROAS: {s_roas.get('prior_30_days', 'N/A')}x"
            
            # Percent Change
            cac_change = s_cac.get('percent_change', 'N/A')
            roas_change = s_roas.get('percent_change', 'N/A')

            # Try to parse to float if it's a string with %
            def parse_change(val):
                if val is None:
                    return None
                if isinstance(val, (int, float)):
                    return val
                try:
                    return float(str(val).replace("%", "").strip())
                except ValueError:
                    return None

            cac_change_val = parse_change(cac_change)
            roas_change_val = parse_change(roas_change)

            
            if cac_change_val is not None:
                trend = "📉" if cac_change_val < 0 else "📈"
                answer += f"• CAC Change: {trend} {cac_change}%"
                
            if roas_change_val is not None:
                trend = "📈" if roas_change_val > 0 else "📉"  
                answer += f"• ROAS Change: {trend} {roas_change}%"
        
        answer += "**Lower CAC + Higher ROAS = Better Performance!**"
        
        # Return JSON for webhook
        result = {
            "success": True,
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        }
        
        print(json.dumps(result))
        return 0
        
    except Exception as e:
        # Error response
        error_result = {
            "success": False,
            "question": question,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        print(json.dumps(error_result))
        return 1

if __name__ == "__main__":
    sys.exit(main())
