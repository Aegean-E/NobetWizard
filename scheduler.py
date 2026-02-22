import calendar
import random
from datetime import date, timedelta
import statistics
import copy

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
        # Also check if the date is in the configured holidays list
        if d.strftime("%d/%m/%Y") in self.config.get('holidays', []):
            return True
        return d.weekday() >= 5

    def get_week_number(self, d):
        return d.isocalendar()[1]

    def check_constraints(self, person, current_date, current_team):
        # 1. Max Duties Total
        # If fixed_duties_total is set (>0), use it as the limit. Otherwise use max_duties.
        fixed_total = person.get('fixed_duties_total', 0)
        limit_total = fixed_total if fixed_total > 0 else person['max_duties']
        
        if person['duty_count'] >= limit_total:
            return False

        # 2. Max Weekend Duties
        if self.is_weekend(current_date):
            fixed_wknd = person.get('fixed_duties_weekend', 0)
            limit_wknd = fixed_wknd if fixed_wknd > 0 else person['max_weekends']
            
            if person['weekend_duty_count'] >= limit_wknd:
                return False

        # 3. Consecutive Days (Yesterday)
        # If they worked yesterday, they cannot work today (unless configured otherwise)
        if not self.config.get('allow_consecutive', False):
            yesterday = current_date - timedelta(days=1)
            
            # Check current month history
            if yesterday in self.schedule:
                if any(p['name'] == person['name'] for p in self.schedule[yesterday]):
                    return False
            # Check previous month history (if we are on day 1)
            elif current_date.day == 1:
                if person['name'] in self.config.get('history', {}).get('prev_1', []):
                    return False
            
            # New Rule: 2 Days Rest (Prevent "Every Other Day" pattern)
            if self.config.get('require_two_rest_days', False):
                day_before = current_date - timedelta(days=2)
                
                # Check current month
                if day_before in self.schedule:
                    if any(p['name'] == person['name'] for p in self.schedule[day_before]):
                        return False
                # Check previous month history
                elif current_date.day == 1:
                    if person['name'] in self.config.get('history', {}).get('prev_2', []):
                        return False
                elif current_date.day == 2:
                    # On day 2, day_before is day 0 (prev_1)
                    if person['name'] in self.config.get('history', {}).get('prev_1', []):
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
        
        # Configurable limit (Default 3)
        if duties_this_week >= self.config.get('max_weekly_duties', 3):
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
            if current_date.strftime("%d/%m/%Y") in [d.strip() for d in off_dates_str.split(',')]:
                return False

        # 8. Leave Dates
        leave_dates_str = person.get('leave_dates', '')
        if leave_dates_str:
            if current_date.strftime("%d/%m/%Y") in [d.strip() for d in leave_dates_str.split(',')]:
                return False

        # 9. Conditional Weekday Rules (e.g., If Wed then No Sat)
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

        # Incompatible Pairs
        # config['forbidden_pairs'] = [{'p1': 'NameA', 'p2': 'NameB'}, ...]
        forbidden_pairs = self.config.get('forbidden_pairs', [])
        if forbidden_pairs and len(team) > 1:
            team_names = set(p['name'] for p in team)
            for pair in forbidden_pairs:
                if pair['p1'] in team_names and pair['p2'] in team_names:
                    return False
        
        # Role / Seniority Constraint
        min_seniors = self.config.get('min_seniors', 0)
        if min_seniors > 0 and len(team) == self.config['people_per_day']:
            seniors_count = sum(1 for p in team if p.get('role') == 'Senior')
            if seniors_count < min_seniors:
                return False
                
        return True

    def generate(self):
        # Reset counts
        for p in self.personnel:
            p['duty_count'] = 0
            p['weekend_duty_count'] = 0

        # Optimization: Find multiple valid schedules and pick the fairest one
        valid_solutions = []
        target_solutions = 5
        max_attempts = 200
        last_error = ""

        for attempt in range(max_attempts):
            self.schedule = {}
            # Reset temp counts for this attempt
            for p in self.personnel:
                p['duty_count'] = 0
                p['weekend_duty_count'] = 0
            
            success = True
            
            # Iterate days
            for day_num in range(1, self.days_in_month + 1):
                current_date = date(self.year, self.month, day_num)
                current_date_str = current_date.strftime("%d/%m/%Y")
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
                def get_sort_key(p):
                    # Priority 0: Needs weekend duty on a weekend
                    if self.is_weekend(current_date):
                        f_wknd = p.get('fixed_duties_weekend', 0)
                        if f_wknd > 0 and p['weekend_duty_count'] < f_wknd:
                            return (0, p['weekend_duty_count'], p['duty_count'])
                    
                    # Priority 1: Needs total duty
                    f_total = p.get('fixed_duties_total', 0)
                    if f_total > 0 and p['duty_count'] < f_total:
                        return (1, p['duty_count'], 0)
                        
                    return (2, p['duty_count'], 0)
                
                candidates.sort(key=get_sort_key)
                
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
                    last_error = f"Could not find enough eligible personnel for {current_date_str}. Found {len(day_team)}/{needed_count}."
                    break
                
                # Commit day
                self.schedule[current_date] = day_team
                for p in day_team:
                    p['duty_count'] += 1
                    if self.is_weekend(current_date):
                        p['weekend_duty_count'] += 1
            
            if success:
                # Calculate Fairness Score (Standard Deviation)
                counts = [p['duty_count'] for p in self.personnel]
                wknd_counts = [p['weekend_duty_count'] for p in self.personnel]
                
                std_total = statistics.stdev(counts) if len(counts) > 1 else 0
                std_wknd = statistics.stdev(wknd_counts) if len(wknd_counts) > 1 else 0
                
                # Combined score: Total variation + Weekend variation
                score = std_total + std_wknd
                
                valid_solutions.append({
                    'schedule': copy.deepcopy(self.schedule),
                    'score': score
                })
                
                if len(valid_solutions) >= target_solutions:
                    break
        
        if valid_solutions:
            # Sort by score (lowest std dev is best)
            valid_solutions.sort(key=lambda x: x['score'])
            best_solution = valid_solutions[0]
            self.schedule = best_solution['schedule']
            
            # Sync counts back to personnel objects so UI stats are accurate
            for p in self.personnel:
                p['duty_count'] = 0
                p['weekend_duty_count'] = 0
                
            for d, team in self.schedule.items():
                for p_sched in team:
                    # Find the original person object to update
                    for p_orig in self.personnel:
                        if p_orig['name'] == p_sched['name']:
                            p_orig['duty_count'] += 1
                            if self.is_weekend(d):
                                p_orig['weekend_duty_count'] += 1
                            break
            
            return True, self.schedule, None
            
        return False, {}, last_error