(define (problem bw_hard_003)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table d)
    (on c a)
    (on e c)
    (clear e)
    (clear b)
    (clear d)
    (handempty)
  )

  (:goal
    (and
      (on b e)
      (on d b)
    )
  )
)
