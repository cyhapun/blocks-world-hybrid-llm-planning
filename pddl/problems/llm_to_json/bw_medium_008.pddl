(define (problem bw_medium_008)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (on_table d)
    (on a b)
    (clear a)
    (clear a)
    (clear c)
    (clear d)
    (handempty)
  )

  (:goal
    (on d a)
  )
)
