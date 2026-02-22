import calendar
import random
from datetime import date, timedelta

class DutyScheduler:
    def __init__(self, year, month, personnel_list, config):
        """
        personnel_list: list of dicts [{'name': '...', 'gender': 'M/F', 'max_duties': 5, 'max_weekends': 2}]
        config: dict {'people_per_day': 2, 'allow_consecutive': False, 'gender_mode': 'Mixed/Single/Any', 'conditional_rules': []}
        """
        self.year = year
        self.month = month
        self.personnel = personnel_list
        self.config = config
        self.days_in_month = calendar.monthrange(year, month)[1]
        self.schedule = {}  # Key: Date, Value: List of names
        self.errors = []

    def is_weekend(self, d):
        # 5 = Saturday, 6 = Sunday
        return d.weekday() >= 5

    def get_week_number(self, d):
        return d.isocalendar()[1]

    def check_constraints(self, person, current_date, current_team):
        # 1. Max Duties Total
        # If fixed_duties is set (>0), use it as the limit. Otherwise use max_duties.
        fixed = person.get('fixed_duties', 0)
        limit = fixed if fixed > 0 else person['max_duties']
        
        if person['duty_count'] >= limit:
            return False

        # 2. Max Weekend Duties
        if self.is_weekend(current_date):
            if person['weekend_duty_count'] >= person['max_weekends']:
                return False

        # 3. Consecutive Days (Yesterday)
        # If they worked yesterday, they cannot work today (unless configured otherwise)
        if not self.config.get('allow_consecutive', False):
            yesterday = current_date - timedelta(days=1)
            if yesterday in self.schedule:
                # Check if person was in yesterday's list
                if any(p['name'] == person['name'] for p in self.schedule[yesterday]):
                    return False
            
            # New Rule: 2 Days Rest (Prevent "Every Other Day" pattern)
            if self.config.get('require_two_rest_days', False):
                day_before = current_date - timedelta(days=2)
                if day_before in self.schedule:
                    if any(p['name'] == person['name'] for p in self.schedule[day_before]):
                        return False

        # 4. Already in current team (cannot be added twice same day)
        if any(p['name'] == person['name'] for p in current_team):
            return False

        # 5. Weekly Constraint (Simple version: Max 2 per week to prevent burnout)
        # This addresses "if x day then y day" by ensuring they don't hold too many in one week
        current_week = self.get_week_number(current_date)
        duties_this_week = 0
        for d, team in self.schedule.items():
            if self.get_week_number(d) == current_week:
                if any(p['name'] == person['name'] for p in team):
                    duties_this_week += 1
        
        # Hard limit of 3 per week to ensure spread, or configurable
        if duties_this_week >= 3:
            return False

        # 6. Busy Days (Day of Week constraint)
        # Checks if the person has blocked this specific day of the week (e.g., "Monday")
        busy_str = person.get('busy_days', '')
        if busy_str:
            busy_list = [d.strip() for d in busy_str.split(',')]
            # Get the day name for the current date (e.g., "Monday")
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][current_date.weekday()]
            if day_name in busy_list:
                return False

        # 7. Specific Off Dates
        off_dates_str = person.get('off_dates', '')
        if off_dates_str:
            if current_date.strftime("%Y-%m-%d") in [d.strip() for d in off_dates_str.split(',')]:
                return False

        # 8. Conditional Weekday Rules (e.g., If Wed then No Sat)
        # config['conditional_rules'] = [{'trigger': 2, 'forbidden': 5}, ...] (0=Mon, 6=Sun)
        conditional_rules = self.config.get('conditional_rules', [])
        if conditional_rules:
            current_weekday = current_date.weekday()
            
            for rule in conditional_rules:
                trigger_day = rule['trigger']
                forbidden_day = rule['forbidden']
                
                # Only check if today is the forbidden day
                if current_weekday == forbidden_day:
                    # Calculate the date of the trigger day in the current week
                    # trigger_date = current_date - (current_weekday - trigger_day)
                    days_diff = current_weekday - trigger_day
                    trigger_date = current_date - timedelta(days=days_diff)
                    
                    # Check if person worked on trigger_date
                    if trigger_date in self.schedule:
                        if any(p['name'] == person['name'] for p in self.schedule[trigger_date]):
                            return False

        return True

    def check_team_constraints(self, team):
        # Gender Rules
        mode = self.config.get('gender_mode', 'Any')
        
        if len(team) == 0:
            return True
            
        genders = [p['gender'] for p in team]
        is_mixed = 'M' in genders and 'F' in genders
        
        if mode == 'Mixed':
            # If team is full, must have both genders. 
            # If not full, we just continue building.
            if len(team) == self.config['people_per_day']:
                if not is_mixed:
                    return False
        
        elif mode == 'Single Gender':
            # All must be same
            if is_mixed:
                return False

        # Personal Constraint: Mixed Gender Preference
        # If the team is mixed, ensure everyone in it allows mixed teams
        if is_mixed:
            for p in team:
                if not p.get('mixed_gender_allowed', True):
                    return False
                
        return True

    def generate(self):
        # Reset counts
        for p in self.personnel:
            p['duty_count'] = 0
            p['weekend_duty_count'] = 0

        # Try to generate schedule multiple times (Monte Carlo / Restart)
        # because greedy algorithms can get stuck
        for attempt in range(100):
            self.schedule = {}
            # Reset temp counts for this attempt
            for p in self.personnel:
                p['duty_count'] = 0
                p['weekend_duty_count'] = 0
            
            success = True
            
            # Iterate days
            for day_num in range(1, self.days_in_month + 1):
                current_date = date(self.year, self.month, day_num)
                current_date_str = current_date.strftime("%Y-%m-%d")
                needed_count = self.config['people_per_day']
                day_team = []
                
                # 1. Handle Fixed Duties (Priority Assignment)
                for p in self.personnel:
                    f_dates = [d.strip() for d in p.get('fixed_dates', '').split(',') if d.strip()]
                    if current_date_str in f_dates:
                        day_team.append(p)
                
                # Shuffle personnel to ensure randomness
                candidates = self.personnel[:]
                random.shuffle(candidates)
                
                # Prioritize people who have a fixed duty target and haven't reached it yet
                # Sort key: 0 = High Priority (Has fixed target > current), 1 = Normal
                candidates.sort(key=lambda p: 0 if (p.get('fixed_duties', 0) > 0 and p['duty_count'] < p.get('fixed_duties', 0)) else 1)
                
                # 2. Fill remaining spots
                for person in candidates:
                    if len(day_team) >= needed_count:
                        break
                    
                    # Skip if already added via fixed duties
                    if any(p['name'] == person['name'] for p in day_team):
                        continue
                    
                    if self.check_constraints(person, current_date, day_team):
                        # Tentatively add
                        day_team.append(person)
                        
                        # Check if adding this person breaks team rules (like gender)
                        # If it's the last person to add, strict check. 
                        # If intermediate, loose check.
                        if not self.check_team_constraints(day_team):
                            day_team.pop() # Backtrack specific person
                        else:
                            # Keep them
                            pass

                # Verify day is full
                if len(day_team) < needed_count:
                    success = False
                    break
                
                # Commit day
                self.schedule[current_date] = day_team
                for p in day_team:
                    p['duty_count'] += 1
                    if self.is_weekend(current_date):
                        p['weekend_duty_count'] += 1
            
            if success:
                return True, self.schedule
        
        return False, {}