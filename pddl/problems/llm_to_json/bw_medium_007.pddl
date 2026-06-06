(define (problem bw_medium_007)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table c)
    (on b a)
    (on d c)
    (clear b)
    (clear d)
    (handempty)
  )

  (:goal
    (on d b)
  )
)
