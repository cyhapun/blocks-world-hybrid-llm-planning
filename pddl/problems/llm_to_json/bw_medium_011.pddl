(define (problem bw_medium_011)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table b)
    (on_table c)
    (on_table d)
    (on a c)
    (clear b)
    (clear a)
    (clear d)
    (handempty)
  )

  (:goal
    (on b a)
  )
)
