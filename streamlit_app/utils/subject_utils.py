from utils.api_client import get_history

def get_subjects(token):
    """
    Get a list of unique subjects from the quiz history.
    
    Args:
        token: JWT authentication token
        
    Returns:
        list: List of unique subject names
    """
    try:
        history = get_history(token)
        if isinstance(history, dict) and 'error' in history:
            return []
            
        # Extract unique subjects
        subjects = set()
        for item in history:
            if isinstance(item, dict) and 'subject' in item and item['subject']:
                subjects.add(str(item['subject']).strip().title())
                
        return sorted(list(subjects))
        
    except Exception as e:
        print(f"Error getting subjects: {str(e)}")
        return []
