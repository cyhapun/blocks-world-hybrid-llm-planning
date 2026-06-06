(define (problem bw_medium_003)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on c a)
    (on d b)
    (clear c)
    (clear d)
    (handempty)
  )

  (:goal
    (on c d)
  )
)
