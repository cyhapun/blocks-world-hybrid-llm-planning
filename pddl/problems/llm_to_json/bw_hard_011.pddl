(define (problem bw_hard_011)
  (:domain blocks-world)

  (:objects
    a b c d e f - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table f)
    (on c a)
    (on e c)
    (on d b)
    (clear e)
    (clear d)
    (clear f)
    (handempty)
  )

  (:goal
    (and
      (on f e)
      (on d c)
    )
  )
)
