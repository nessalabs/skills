---- MODULE TraceTraversal ----
EXTENDS Naturals, Sequences, FiniteSets
VARIABLES stack, seen, emitted, limit
vars == <<stack,seen,emitted,limit>>
Children(n) == CASE n = "A" -> <<"B","C">> [] n = "B" -> <<"D">>
                    [] n = "C" -> <<"D">> [] OTHER -> <<"A">>
Push(n,d) == [i \in 1..Len(Children(n)) |-> [node |-> Children(n)[i], depth |-> d+1]]
Init == /\ limit \in {2,3} /\ stack = <<[node |-> "A",depth |-> 1]>>
        /\ seen = {} /\ emitted = <<>>
Visit == /\ Len(stack)>0 /\ Head(stack).node \notin seen
         /\ seen' = seen \cup {Head(stack).node}
         /\ emitted' = Append(emitted,Head(stack))
         /\ stack' = IF Head(stack).depth < limit THEN Push(Head(stack).node,Head(stack).depth) \o Tail(stack) ELSE Tail(stack)
         /\ UNCHANGED limit
Skip == /\ Len(stack)>0 /\ Head(stack).node \in seen
        /\ stack' = Tail(stack) /\ UNCHANGED <<seen,emitted,limit>>
Next == Visit \/ Skip
UniqueEmission == Len(emitted) = Cardinality({emitted[i].node : i \in 1..Len(emitted)})
DepthBound == \A i \in 1..Len(emitted) : emitted[i].depth <= limit
====
