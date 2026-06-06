(define (problem bw_medium_002)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table c)
    (on_table d)
    (on b a)
    (clear b)
    (clear c)
    (clear d)
    (handempty)
  )

  (:goal
    (on d b)
  )
)
