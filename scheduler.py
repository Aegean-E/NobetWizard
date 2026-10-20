import calendar
import random
from datetime import date, datetime, timedelta
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
        self._fixed_dates_by_person = {}
        self._fixed_week_counts = {}
        self._fixed_baseline = {}

    def is_weekend(self, d):
        # 5 = Saturday, 6 = Sunday
        # Also check if the date is in the configured holidays list
        if d.strftime("%d/%m/%Y") in self.config.get('holidays', []):
            return True
        return d.weekday() >= 5

    def get_week_number(self, d):
        return d.isocalendar()[1]

    def _split_dates(self, person, field):
        raw = person.get(field, '')
        if not raw:
            return set()
        if isinstance(raw, (list, tuple, set)):
            return {str(item).strip() for item in raw if str(item).strip()}
        return {item.strip() for item in str(raw).split(',') if item.strip()}

    def _is_fixed_on(self, person_name, d):
        return d in self._fixed_dates_by_person.get(person_name, set())

    def _duties_in_week(self, person_name, week):
        total = self._fixed_week_counts.get(person_name, {}).get(week, 0)
        for d, team in self.schedule.items():
            if self.get_week_number(d) != week:
                continue
            if self._is_fixed_on(person_name, d):
                continue
            if any(p['name'] == person_name for p in team):
                total += 1
        return total

    def _reset_counters(self):
        for p in self.personnel:
            p['duty_count'] = 0
            p['weekend_duty_count'] = 0
            p['saturday_duty_count'] = 0
            p['sunday_duty_count'] = 0

    def _increment_fixed(self, person, d):
        person['duty_count'] += 1
        if self.is_weekend(d):
            person['weekend_duty_count'] += 1
            if d.weekday() == 5:
                person['saturday_duty_count'] += 1
            elif d.weekday() == 6:
                person['sunday_duty_count'] += 1
        week = self.get_week_number(d)
        weeks = self._fixed_week_counts.setdefault(person['name'], {})
        weeks[week] = weeks.get(week, 0) + 1

    def _restore_baseline(self):
        for p in self.personnel:
            baseline = self._fixed_baseline.get(p['name'], {})
            p['duty_count'] = baseline.get('duty_count', 0)
            p['weekend_duty_count'] = baseline.get('weekend_duty_count', 0)
            p['saturday_duty_count'] = baseline.get('saturday_duty_count', 0)
            p['sunday_duty_count'] = baseline.get('sunday_duty_count', 0)

    def _index_fixed_duties(self):
        index = {}
        for person in self.personnel:
            dates = set()
            for raw in self._split_dates(person, 'fixed_dates'):
                try:
                    parsed = datetime.strptime(raw, "%d/%m/%Y").date()
                except ValueError:
                    return None, (f"Fixed duty date '{raw}' for '{person['name']}' is not DD/MM/YYYY.")
                if parsed.year == self.year and parsed.month == self.month:
                    dates.add(parsed)
            index[person['name']] = dates
        return index, None

    def _validate_fixed_duties(self):
        """
        Commit every fixed duty first: a fixed duty that breaks availability, rest,
        weekly, max-duty or team rules is reported by name and date instead of being
        forced into the roster (it used to bypass every constraint).
        """
        self.schedule = {}
        self._reset_counters()
        self._fixed_week_counts = {}
        people_per_day = self.config['people_per_day']
        by_day = {}
        for name, dates in self._fixed_dates_by_person.items():
            for d in dates:
                by_day.setdefault(d, []).append(name)

        for day in range(1, self.days_in_month + 1):
            d = date(self.year, self.month, day)
            names = by_day.get(d)
            if not names:
                continue
            if len(names) > people_per_day:
                return (f"Fixed duties on {d.strftime('%d/%m/%Y')} assign {len(names)} people; "
                        f"at most {people_per_day} per day are allowed.")
            team = []
            for name in names:
                person = next(p for p in self.personnel if p['name'] == name)
                if not self.check_constraints(person, d, team):
                    return (f"Fixed duty for '{name}' on {d.strftime('%d/%m/%Y')} violates "
                            "availability, rest, weekly or max-duty rules.")
                team.append(person)
            if len(team) == people_per_day and not self.check_team_constraints(team):
                return (f"Fixed duties on {d.strftime('%d/%m/%Y')} violate gender, "
                        "seniority or incompatible-pair rules.")
            self.schedule[d] = team
            for person in team:
                self._increment_fixed(person, d)

        self._fixed_baseline = {
            p['name']: {
                'duty_count': p['duty_count'],
                'weekend_duty_count': p['weekend_duty_count'],
                'saturday_duty_count': p['saturday_duty_count'],
                'sunday_duty_count': p['sunday_duty_count'],
            }
            for p in self.personnel
        }
        self.schedule = {}
        return None

    def check_constraints(self, person, current_date, current_team):
        # 1. Max Duties Total
        # If fixed_duties_total is set (>0), use it as the limit. Otherwise use max_duties.
        fixed_total = person.get('fixed_duties_total', 0)
        limit_total = fixed_total if fixed_total > 0 else person.get('max_duties', 0)
        
        if person['duty_count'] >= limit_total:
            return False

        # 2. Max Weekend Duties
        if self.is_weekend(current_date):
            fixed_wknd = person.get('fixed_duties_weekend', 0)
            limit_wknd = fixed_wknd if fixed_wknd > 0 else person.get('max_weekends', 0)
            
            if person['weekend_duty_count'] >= limit_wknd:
                return False

        allow_consecutive = self.config.get('allow_consecutive', False)
        require_two_rest = self.config.get('require_two_rest_days', False)

        # 3. Consecutive Days (Yesterday and tomorrow's fixed duty)
        if not allow_consecutive:
            yesterday = current_date - timedelta(days=1)
            
            # Check current month history
            if yesterday in self.schedule:
                if any(p['name'] == person['name'] for p in self.schedule[yesterday]):
                    return False
            # Check previous month history (if we are on day 1)
            elif current_date.day == 1:
                if person['name'] in self.config.get('history', {}).get('prev_1', []):
                    return False

            # A fixed duty tomorrow would also be a back-to-back assignment.
            if self._is_fixed_on(person['name'], current_date + timedelta(days=1)):
                return False

        # 4. 2 Days Rest (independent of Allow Consecutive)
        if require_two_rest:
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

            # A fixed duty two days ahead would break the rest window.
            if self._is_fixed_on(person['name'], current_date + timedelta(days=2)):
                return False

        # 5. Already in current team (cannot be added twice same day)
        if any(p['name'] == person['name'] for p in current_team):
            return False

        # 6. Weekly Constraint (Mon-Sun; fixed duties are reserved up front)
        current_week = self.get_week_number(current_date)
        duties_this_week = self._duties_in_week(person['name'], current_week)
        
        # Configurable limit (Default 3)
        if duties_this_week >= self.config.get('max_weekly_duties', 3):
            return False

        # 7. Busy Days (Day of Week constraint)
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
                    # Walk back to this week's trigger day, wrapping across weeks
                    days_diff = (current_weekday - trigger_day) % 7
                    trigger_date = current_date - timedelta(days=days_diff)
                    
                    # Check if person worked on trigger_date
                    if trigger_date in self.schedule:
                        if any(p['name'] == person['name'] for p in self.schedule[trigger_date]):
                            return False

        # 10. Weekend Balance (Sat vs Sun)
        # Ensure that a person doesn't accumulate too many Saturdays without Sundays and vice versa.
        if current_date.weekday() == 5: # Saturday
            if person.get('saturday_duty_count', 0) > person.get('sunday_duty_count', 0):
                return False
        elif current_date.weekday() == 6: # Sunday
            if person.get('sunday_duty_count', 0) > person.get('saturday_duty_count', 0):
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
            # A one-person shift can never contain both genders.
            if len(team) == self.config['people_per_day'] and self.config['people_per_day'] > 1:
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
        # Fixed duties are validated and reserved before the randomized fill so they
        # cannot bypass availability, rest, weekly, max-duty or team rules.
        index, index_error = self._index_fixed_duties()
        if index_error:
            return False, {}, index_error
        self._fixed_dates_by_person = index
        fixed_error = self._validate_fixed_duties()
        if fixed_error:
            return False, {}, fixed_error

        # Optimization: Find multiple valid schedules and pick the fairest one
        valid_solutions = []
        target_solutions = 5
        max_attempts = 200
        last_error = ""

        for attempt in range(max_attempts):
            self.schedule = {}
            # Fixed duties are already counted; restore that baseline for this attempt
            self._restore_baseline()
            
            success = True
            
            # Iterate days
            for day_num in range(1, self.days_in_month + 1):
                current_date = date(self.year, self.month, day_num)
                current_date_str = current_date.strftime("%d/%m/%Y")
                needed_count = self.config['people_per_day']
                day_team = []
                
                # 1. Handle Fixed Duties (validated up front)
                for p in self.personnel:
                    if self._is_fixed_on(p['name'], current_date):
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
                
                # Commit day (fixed duties already sit in the baseline counts)
                self.schedule[current_date] = day_team
                for p in day_team:
                    if self._is_fixed_on(p['name'], current_date):
                        continue
                    p['duty_count'] += 1
                    if self.is_weekend(current_date):
                        p['weekend_duty_count'] += 1
                        if current_date.weekday() == 5:
                            p['saturday_duty_count'] += 1
                        elif current_date.weekday() == 6:
                            p['sunday_duty_count'] += 1
            
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
                p['saturday_duty_count'] = 0
                p['sunday_duty_count'] = 0
                
            for d, team in self.schedule.items():
                for p_sched in team:
                    # Find the original person object to update
                    for p_orig in self.personnel:
                        if p_orig['name'] == p_sched['name']:
                            p_orig['duty_count'] += 1
                            if self.is_weekend(d):
                                p_orig['weekend_duty_count'] += 1
                                if d.weekday() == 5:
                                    p_orig['saturday_duty_count'] = p_orig.get('saturday_duty_count', 0) + 1
                                elif d.weekday() == 6:
                                    p_orig['sunday_duty_count'] = p_orig.get('sunday_duty_count', 0) + 1
                            break
            
            return True, self.schedule, None
            
        return False, {}, last_error