# class_catch_app/filters.py
from django.db.models.functions import Cast
from django.db.models import IntegerField, Func, F, Value, Q
from django_filters import rest_framework as filters
from urllib.parse import unquote
from .models import Class


class RegexReplace(Func):
    function = "REGEXP_REPLACE"
    template = "%(function)s(%(expressions)s)"


class ClassFilter(filters.FilterSet):
    """
    A custom FilterSet for complex logic:
     - 'terms' => OR logic
     - 'distribs' => AND intersection
     - 'world_cultures' => AND intersection
     - 'lang_reqs' => AND intersection
     - 'periods' => OR logic
    Then across categories => combine results with AND (that is how FilterSet chain works).
    """

    # extra filter fields for numeric ranges
    course_number__gte = filters.NumberFilter(
        method='filter_course_number_gte')
    course_number__lte = filters.NumberFilter(
        method='filter_course_number_lte')

    terms = filters.CharFilter(method='filter_terms')
    distribs = filters.CharFilter(method='filter_distribs')
    world_cultures = filters.CharFilter(method='filter_world_cultures')
    lang_reqs = filters.CharFilter(method='filter_lang_reqs')
    periods = filters.CharFilter(method='filter_periods')
    class_code = filters.CharFilter(field_name="class_code", lookup_expr="exact")
    
    # class code specific filtering
    or_filter = filters.CharFilter(method='filter_or')
    allowed = filters.CharFilter(method='filter_allowed')


    class Meta:
        model = Class
        fields = []  # all handled in custom methods

    def filter_terms(self, queryset, name, value):
        """
        If 'terms=202501,202409', we do an OR:
          (term=202501) OR (term=202409)
        This is done with "term__in".
         log debugging info about the final query.
        """
        if not value:
            return queryset
        term_list = [t.strip() for t in value.split(',') if t.strip()]
        if not term_list:
            return queryset

        # OR among multiple terms => __in does that automatically
        new_queryset = queryset.filter(term__in=term_list)
        print("[DEBUG] filter_terms OR logic for:", term_list)
        print("[DEBUG] Resulting SQL for terms:", new_queryset.query)
        return new_queryset

    def filter_distribs(self, queryset, name, value):
        """
        If 'distribs=ART,LIT', we want an intersection:
         - Class must have 'ART' in its distrib field AND 'LIT' in its distrib field
        We do repeated 'filter(distrib__icontains=...)'.
         log debug info.
        """
        if not value:
            return queryset
        codes = [d.strip() for d in value.split(',') if d.strip()]

        print("[DEBUG] filter_distribs intersection for:", codes)
        for code in codes:
            queryset = queryset.filter(distrib__icontains=code)
            print(f"[DEBUG] After requiring '{
                  code}' in distrib:", queryset.query)
        return queryset

    def filter_world_cultures(self, queryset, name, value):
        """
        If 'world_cultures=W,CI', intersection => must contain W AND CI.
        Again, repeated icontains calls.
        """
        if not value:
            return queryset
        codes = [wc.strip() for wc in value.split(',') if wc.strip()]

        print("[DEBUG] filter_world_cultures intersection for:", codes)
        for code in codes:
            queryset = queryset.filter(world_culture__icontains=code)
            print(f"[DEBUG] After requiring '{
                  code}' in world_culture:", queryset.query)
        return queryset

    def filter_lang_reqs(self, queryset, name, value):
        """
        If 'lang_reqs=LADV,LACC', intersection => must contain LADV AND LACC in 'lang_req'.
         do substring matching the same way as 'distrib'.
        """
        if not value:
            return queryset
        codes = [lr.strip() for lr in value.split(',') if lr.strip()]

        print("[DEBUG] filter_lang_reqs intersection for:", codes)
        for code in codes:
            queryset = queryset.filter(lang_req__icontains=code)
            print(f"[DEBUG] After requiring '{
                  code}' in lang_req:", queryset.query)
        return queryset

    def filter_periods(self, queryset, name, value):
        """
        If 'periods=10,10A,12', we want a union:
          (period == 10) OR (period == 10A) OR (period == 12)
        So  do period_code__in=[list].
         do an OR in a single line by 'filter(period_code__in=list)'.
        """
        if not value:
            return queryset
        period_list = [p.strip() for p in value.split(',') if p.strip()]
        if not period_list:
            return queryset

        # exact matching => if your DB stores period exactly "10A" or "12"
        new_queryset = queryset.filter(period_code__in=period_list)

        print("[DEBUG] filter_periods OR logic for:", period_list)
        print("[DEBUG] Resulting SQL for periods:", new_queryset.query)
        return new_queryset

    def filter_course_number_gte(self, queryset, name, value):
        """
        Return rows where int(course_number) >= value, ignoring any rows with non-integer course_number.
        """
        if value is None:
            return queryset

        # attempt to cast course_number to an integer at the SQL level
        queryset = queryset.annotate(
            # replace everything after the decimal in 'course_number'
            digits_only=RegexReplace(
                F('course_number'),
                # pattern: matches '.' and everything after
                Value(r'\..*'),
                # replace matched content with an empty string
                Value('')
            )
        )
        # cast digits_only to int
        queryset = queryset.annotate(
            course_num_int=Cast('digits_only', IntegerField())
        )
        # filter
        new_qs = queryset.filter(course_num_int__gte=value)

        print(f"[DEBUG] filter_course_number_gte >= { value}, total after filtering: {new_qs.count()}")
        return new_qs

    def filter_course_number_lte(self, queryset, name, value):
        """
        Return rows where int(course_number) <= value, ignoring rows with non-integer course_number.
        """
        if value is None:
            return queryset

        queryset = queryset.annotate(
            # replace everything after the decimal in 'course_number'
            digits_only=RegexReplace(
                F('course_number'), 
                # pattern: matches '.' and everything after
                Value(r'\..*'),
                # replace matched content with an empty string
                Value('')
            )
        )
        # cast digits_only to int
        queryset = queryset.annotate(
            course_num_int=Cast('digits_only', IntegerField())
        )
        # filter
        new_qs = queryset.filter(course_num_int__lte=value)

        print(f"[DEBUG] filter_course_number_lte <= {value}, total after filtering: {new_qs.count()}")
        return new_qs
   
    def filter_allowed(self, queryset, name, value):
        print("[DEBUG filter_allowed] GOT CALLED with param:", name, "value:", value)
        """
        If 'allowed=COSC1,ENGS20', we interpret that as an OR:
        (class_code='COSC', course_number ~ some pattern matching '1','01','001', plus decimals)
        (class_code='ENGS', course_number='20', etc.)

        We handle leading zeros for the integer part, and if there's a decimal part, we match it exactly.
        E.g. 'COSC69.12' => prefix='COSC', num='69.12' => we match '^0*69(\.12)?$'
        """
        tokens = [t.strip() for t in value.split(",") if t.strip()]
        if not tokens:
            return queryset

        or_query = Q()

        for token in tokens:
            # separate alpha prefix from the rest
            prefix = "".join([c for c in token if c.isalpha()])
            numeric_part = token[len(prefix):]  # everything after the letters

            # e.g. prefix='COSC', numeric_part='001', or '69.12'
            # numeric_part is empty => no match
            if not prefix or not numeric_part:
                continue

            # separate the integer portion from optional decimal
            # For example: '69.12' => integer='69', decimal='.12'
            # '001' => integer='001', decimal=''
            dot_index = numeric_part.find(".")
            if dot_index >= 0:
                integer_part = numeric_part[:dot_index]
                decimal_part = numeric_part[dot_index:]  # includes the dot, e.g. ".12"
            else:
                integer_part = numeric_part
                decimal_part = ""

            # remove leading zeros from the integer_part (for matching)
            if all(ch == '0' for ch in integer_part):
                # e.g. '000' => '0'
                stripped_int = "0"
            else:
                stripped_int = integer_part.lstrip('0')  # e.g. '001' => '1'

            # build a regex that matches '^0*{stripped_int}{decimal_part}?$'
            import re

            # escape the decimal_part
            dec_esc = re.escape(decimal_part)  # e.g. ".12" => "\.12"
            if decimal_part:
                pattern = f"^0*{re.escape(stripped_int)}{dec_esc}$"
            else:
                pattern = f"^0*{re.escape(stripped_int)}$"

            print(f"[DEBUG] allowed token={token}, prefix={prefix}, integer={integer_part}, decimal={decimal_part}, pattern={pattern}")

            or_query |= Q(class_code=prefix, course_number__regex=pattern)

        print("[DEBUG] filter_allowed => tokens:", tokens, " => or_query:", or_query)
        return queryset.filter(or_query) if or_query else queryset

    
    def filter_or(self, queryset, name, value):
        print("[DEBUG filter_or] GOT CALLED with param:", name, "value:", value)
        """
        e.g. ?or=class_code%3DCOSC%26min_number%3D30%26max_number%3D89%7Cclass_code%3DMATH%26min_number%3D20
        => decode => 'class_code=COSC&min_number=30&max_number=89|class_code=MATH&min_number=20'
        => split on '|'
        => each sub => parse 'class_code=COSC&min_number=30...' => build Q => or_query |= sub_q
        """
        if not value:
            return queryset
        
        print("[DEBUG] filter_or => raw param from request:", value)

        # decode
        decoded = unquote(value)
        print("[DEBUG] filter_or => after unquote =>", decoded)

        # decode it => 'class_code=COSC&min_number=30...|class_code=MATH&min_number=20'
        or_parts = decoded.split("|")  # => [ "class_code=COSC&min_number=30...", "class_code=MATH&min_number=20"]
        print("[DEBUG] filter_or => or_parts =>", or_parts)
        
        or_query = Q()
        for part in or_parts:
            print("[DEBUG] sub-part =>", part)
            sub_q = Q()
            sub_params = part.split("&")  # => ["class_code=COSC","min_number=30","max_number=89"]
            for p in sub_params:
                if "=" in p:
                    k, v = p.split("=", 1)
                    print(f"[DEBUG] sub_param => key={k}, value={v}")
                    if k == "class_code":
                        sub_q &= Q(class_code=v)
                    elif k == "min_number":
                        queryset = self._annotateCourseNumberAsInt(queryset)
                        sub_q &= Q(course_num_int__gte=int(v))
                    elif k == "max_number":
                        queryset = self._annotateCourseNumberAsInt(queryset)
                        sub_q &= Q(course_num_int__lte=int(v))
                    elif k == "course_number":
                        sub_q &= Q(course_number=v)
            print("[DEBUG] sub_q =>", sub_q)
            or_query |= sub_q

        print("[DEBUG] or_query =>", or_query)

        final_qs = queryset.filter(or_query)
        print("[DEBUG] final_qs.count() =>", final_qs.count())
        print("[DEBUG] final_qs.query =>", final_qs.query)
        return final_qs

    def _annotateCourseNumberAsInt(self, qs):
        """
        Helper to replicate your numeric logic:
        strips decimals, cast to int => course_num_int
        """
        qs = qs.annotate(
            digits_only=RegexReplace(
                F('course_number'),
                Value(r'\..*'),
                Value('')
            )
        ).annotate(
            course_num_int=Cast('digits_only', IntegerField())
        )
        return qs