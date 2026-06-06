(define (problem bw_medium_001)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (on_table d)
    (clear a)
    (clear b)
    (clear c)
    (clear d)
    (handempty)
  )

  (:goal
    (and
      (on a b)
      (on c d)
    )
  )
)
